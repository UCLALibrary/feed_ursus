# -*- coding: utf-8 -*-
"""
Import JSON data into https://sinaimanuscripts.library.ucla.edu/

Input files are stored in https://github.com/UCLALibrary/sinaiportal_data
Output is pushed to a solr index suitable for use by https://github.com/UCLALibrary/sinaimanuscripts
"""

import asyncio
import json
import logging
from math import inf
from pathlib import Path
from typing import Any, Awaitable, Iterator, Optional

import httpx
import rich.progress
from pysolr import Solr, SolrError  # type: ignore

import feed_sinai.sinai_types as st
from feed_sinai.solr_record import ManuscriptSolrRecord


class SinaiJsonImporter:
    """Importer class to map data from"""

    base_path: Path
    solr: Solr
    solr_url: str | None
    async_client = httpx.AsyncClient()
    connection_pool = asyncio.Semaphore(3)

    _ms_objs_merged: dict[Path, st.ManuscriptObjectMerged]

    def __init__(self, base_path: str = ".", solr_url: Optional[str] = None):
        self.base_path = Path(base_path)
        self.solr = Solr(solr_url, always_commit=True)
        self.solr_url = solr_url

        self._ms_objs_merged = dict()

    @staticmethod
    def get_filename(ark: str) -> str:
        """Returns a filename based on an item's ark.

        Drops "ark:/21198/" (all records are assigned the UCLA NAAN) and adds the ".json" suffix"
        """

        return ark.replace("ark:/21198/", "").replace("/", "-") + ".json"

    def get_agent(self, ark: str) -> st.Agent:
        path = self.base_path / "agents" / self.get_filename(ark)
        return st.Agent.model_validate_json(path.read_text())

    def get_place(self, ark: str) -> st.Place:
        path = self.base_path / "places" / self.get_filename(ark)
        return st.Place.model_validate_json(path.read_text())

    def get_assoc_place_item(
        self, raw: st.AssocPlaceItemUnmerged
    ) -> st.AssocPlaceItemMerged:
        return raw.convert(
            st.AssocPlaceItemMerged,
            place_record=self.get_place(raw.id) if raw.id else None,
        )

    def get_assoc_name_item(
        self, raw: st.AssocNameItemUnmerged
    ) -> st.AssocNameItemMerged:
        return raw.convert(
            st.AssocNameItemMerged,
            agent_record=self.get_agent(raw.id) if raw.id else None,
        )

    def get_conceptual_work(self, stub: st.WorkStub) -> st.ConceptualWorkMerged:
        path = self.base_path / "works" / self.get_filename(stub.id)
        raw = st.ConceptualWorkUnmerged.model_validate_json(path.read_text())

        return raw.convert(
            st.ConceptualWorkMerged,
            creator=[
                self.get_assoc_name_item(assoc_name) for assoc_name in raw.creator
            ],
        )

    def get_work_brief(self, raw: st.WorkBriefUnmerged) -> st.WorkBriefMerged:
        return raw.convert(
            st.WorkBriefMerged,
            creator=[
                st.WorkBriefCreator(id=id, agent_record=self.get_agent(id))
                for id in raw.creator
            ],
        )

    def get_contents_item(self, raw: st.ContentsUnmerged) -> st.ContentsMerged:
        if not raw.work_id:
            return raw.convert(st.ContentsMerged)

        work_record = self.get_conceptual_work(stub=st.WorkStub(id=raw.work_id))

        return raw.convert(st.ContentsMerged, pref_title=work_record.pref_title)

    def get_work_wit(self, raw: st.WorkWitItemUnmerged) -> st.WorkWitItemMerged:
        return raw.convert(
            st.WorkWitItemMerged,
            work=(
                self.get_work_brief(raw.work)
                if isinstance(raw.work, st.WorkBrief)
                else self.get_conceptual_work(raw.work)
            ),
            contents=[self.get_contents_item(raw_item) for raw_item in raw.contents],
        )

    def get_para(self, raw: st.ParaItemUnmerged) -> st.ParaItemMerged:
        return raw.convert(
            st.ParaItemMerged,
            assoc_name=[self.get_assoc_name_item(name) for name in raw.assoc_name],
            assoc_place=[self.get_assoc_place_item(place) for place in raw.assoc_place],
        )

    def get_text_unit(self, ark: st.Ark) -> st.TextUnitMerged:
        path = self.base_path / "text_units" / self.get_filename(ark)
        raw = st.TextUnitUnmerged.model_validate_json(path.read_text())

        return raw.convert(
            st.TextUnitMerged,
            work_wit=[self.get_work_wit(work_wit) for work_wit in raw.work_wit],
            para=[self.get_para(para) for para in raw.para],
            reconstructed_from=[
                st.ReconstructedFrom(
                    id=ark, shelfmark=self.get_merged_manuscript(ark).shelfmark
                )
                for ark in raw.reconstructed_from
            ],
        )

    def get_layer_text_unit(
        self, raw: st.LayerTextUnitUnmerged
    ) -> st.LayerTextUnitMerged:
        return raw.convert(
            st.LayerTextUnitMerged, text_unit_record=self.get_text_unit(raw.id)
        )

    def get_uto_ms_ark(self, layer_record: st.InscribedLayerMerged) -> st.Ark | None:
        arks: list[st.Ark] = []
        for parent_ark in layer_record.parent:
            parent_ms = st.ManuscriptObjectUnmerged.model_validate_json(
                (self.base_path / "ms_objs" / self.get_filename(parent_ark)).read_text()
            )
            if parent_ms.type.id == "uto":
                arks.append(parent_ark)

        if len(arks) == 0:
            return None

        if len(arks) > 1:
            logging.warning(
                f"Multiple values found for `uto_ms_ark` in {layer_record}, using the first and discarding the rest"
            )

        return arks[0]

    def get_layer(
        self, ms_layer: st.ManuscriptLayerUnmerged
    ) -> st.ManuscriptLayerMerged:
        assert ms_layer.type.id != "undertext"

        layer_record_path = self.base_path / "layers" / self.get_filename(ms_layer.id)
        raw = st.InscribedLayerUnmerged.model_validate_json(
            layer_record_path.read_text()
        )

        layer_record = raw.convert(
            st.InscribedLayerMerged,
            text_unit=[
                self.get_layer_text_unit(text_unit) for text_unit in raw.text_unit
            ],
            para=[self.get_para(para) for para in raw.para],
            assoc_name=[
                self.get_assoc_name_item(name_item) for name_item in raw.assoc_name
            ],
            assoc_place=[self.get_assoc_place_item(place) for place in raw.assoc_place],
            reconstructed_from=[
                st.ReconstructedFrom(
                    id=ark, shelfmark=self.get_merged_manuscript(ark).shelfmark
                )
                for ark in raw.reconstructed_from
            ],
        )

        return ms_layer.convert(st.ManuscriptLayerMerged, layer_record=layer_record)

    def get_uto(
        self, ms_layer: st.ManuscriptLayerUnmerged
    ) -> st.ManuscriptLayerMerged | st.UndertextManuscriptLayerMerged:
        assert ms_layer.type.id == "undertext"

        layer_record_path = self.base_path / "layers" / self.get_filename(ms_layer.id)
        raw = st.InscribedLayerUnmerged.model_validate_json(
            layer_record_path.read_text()
        )

        layer_record = raw.convert(
            st.InscribedLayerMerged,
            text_unit=[
                self.get_layer_text_unit(text_unit) for text_unit in raw.text_unit
            ],
            para=[self.get_para(para) for para in raw.para],
            assoc_name=[
                self.get_assoc_name_item(name_item) for name_item in raw.assoc_name
            ],
        )

        return ms_layer.convert(
            st.UndertextManuscriptLayerMerged,
            uto_ms_ark=self.get_uto_ms_ark(layer_record),
            script=[
                script.label
                for writing_item in layer_record.writing
                for script in writing_item.script
            ],
            lang=[
                lang.label
                for text_unit in layer_record.text_unit
                for lang in text_unit.text_unit_record.lang
            ],
            orig_date=[
                date
                for date in (layer_record.assoc_date or [])
                if date.type.id == "origin"
            ],
        )

    def get_part(self, raw: st.PartUnmerged) -> st.PartMerged:
        return raw.convert(
            st.PartMerged,
            layer=[],
            ot_layer=[
                self.get_layer(layer)
                for layer in raw.layer
                if layer.type.id == "overtext"
            ],
            guest_layer=[
                self.get_layer(layer) for layer in raw.layer if layer.type.id == "guest"
            ],
            uto=[
                self.get_uto(layer)
                for layer in raw.layer
                if layer.type.id == "undertext"
            ],
            para=[self.get_para(para) for para in raw.para],
        )

    def get_merged_manuscript(
        self, path_or_ark: Path | str
    ) -> st.ManuscriptObjectMerged:
        if isinstance(path_or_ark, str):
            path = (
                self.base_path
                / "ms_objs"
                / (path_or_ark.removeprefix("ark:/21198/") + ".json")
            )
        else:
            path = path_or_ark

        if path in self._ms_objs_merged:
            return self._ms_objs_merged[path]

        raw = st.ManuscriptObjectUnmerged.model_validate_json(path.read_text())

        self._ms_objs_merged[path] = raw.convert(
            st.ManuscriptObjectMerged,
            part=[self.get_part(stub) for stub in raw.part],
            layer=[],
            ot_layer=[
                self.get_layer(layer)
                for layer in raw.layer
                if layer.type.id == "overtext"
            ],
            guest_layer=[
                self.get_layer(layer) for layer in raw.layer if layer.type.id == "guest"
            ],
            uto=[
                self.get_uto(layer)
                for layer in raw.layer
                if layer.type.id == "undertext"
            ],
            assoc_name=[self.get_assoc_name_item(name) for name in raw.assoc_name],
            assoc_place=[self.get_assoc_place_item(place) for place in raw.assoc_place],
            para=[self.get_para(para) for para in raw.para],
            reconstructed_from=[
                st.ReconstructedFrom(
                    id=ark, shelfmark=self.get_merged_manuscript(ark).shelfmark
                )
                for ark in raw.reconstructed_from
            ],
        )

        return self._ms_objs_merged[path]

    def iterate_merged_records(self) -> Iterator[st.ManuscriptObjectMerged]:
        """Yield json records for manuscripts with other data embedded."""

        paths = tuple((self.base_path / "ms_objs").glob("*.json"))
        for path in rich.progress.track(paths):
            try:
                yield self.get_merged_manuscript(path)
            except Exception as e:
                logging.warning(f"Could not merge {path}: {e}")

    def save_merged_records(self) -> None:
        (self.base_path / "merged").mkdir(exist_ok=True)
        for record in self.iterate_merged_records():
            path = self.base_path / "merged" / self.get_filename(record.ark)
            path.write_text(record.model_dump_json(indent=2))

    def solr_record(self, ms_obj: st.ManuscriptObjectMerged) -> dict[str, Any]:
        return json.loads(ManuscriptSolrRecord(ms_obj=ms_obj).model_dump_json())

    async def load_to_solr(self, batch_size: float = inf) -> None:
        """
        Loads records to Solr in batches. `batch_size` should be a positive integer or `math.inf`.
        """
        batch: list[dict] = list()
        results: list[Awaitable[None]] = list()

        for record in self.iterate_merged_records():
            try:
                batch.append(self.solr_record(record))
            except Exception as e:
                logging.warning(f"could not generate solr document {record.ark}: {e}")

            if len(batch) > 100:
                results.append(self.add_batch(batch))
                batch = list()

        if len(batch) > 0:
            results.append(self.add_batch(batch))

        await asyncio.gather(*results)

    async def add_batch(self, batch: list[dict]) -> None:
        try:
            async with self.connection_pool:
                response = await self.async_client.post(
                    f"{self.solr_url}/update?commit=true", json=batch
                )

            if response.is_error:
                raise SolrError(response.json().get("error").get("msg"))

        except Exception as e:
            if len(batch) == 1:
                print(f"Error adding record {batch[0]['id']}: {e}")
            else:
                mid = int(len(batch) / 2)
                await asyncio.gather(
                    self.add_batch(batch[:mid]), self.add_batch(batch[mid:])
                )

    def save_solr_records(self) -> None:
        (self.base_path / "solr").mkdir(exist_ok=True)
        for record in self.iterate_merged_records():
            path = self.base_path / "solr" / self.get_filename(record.ark)
            path.write_text(
                ManuscriptSolrRecord(ms_obj=record).model_dump_json(indent=2)
            )

    def wipe_solr_records(self) -> None:
        self.solr.delete(q="*:*")
