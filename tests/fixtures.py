# pylint: disable=all
# mypy: disallow_untyped_defs=False


class MockResponse:
    def __init__(self, status_code, json_data):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


GOOD_MANIFEST = MockResponse(
    200,
    {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "label": "Sinai Arabic 352. Mimars and Lives of Saints : manuscript, 1200. St. Catherine's Monastery, Sinai, Egypt",
        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest",
        "@type": "sc:Manifest",
        "sequences": [
            {
                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/sequence/normal",
                "@type": "sc:Sequence",
                "canvases": [
                    {
                        "@type": "sc:Canvas",
                        "label": "Front Board Outside",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/hm957748",
                        "width": 5332,
                        "height": 7006,
                        "images": [
                            {
                                "@type": "oa:Annotation",
                                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/annotation/hm957748",
                                "motivation": "sc:painting",
                                "on": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/hm957748",
                                "resource": {
                                    "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fhm957748/full/600,/0/default.jpg",
                                    "@type": "dctypes:Image",
                                    "format": "image/jpeg",
                                    "service": {
                                        "@context": "http://iiif.io/api/image/2/context.json",
                                        "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fhm957748",
                                        "profile": "http://iiif.io/api/image/2/level0.json",
                                    },
                                },
                            }
                        ],
                    },
                    {
                        "@type": "sc:Canvas",
                        "label": "f. 001r",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/zw07hs0c",
                        "width": 5332,
                        "height": 7008,
                        "images": [
                            {
                                "@type": "oa:Annotation",
                                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/annotation/zw07hs0c",
                                "motivation": "sc:painting",
                                "on": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/zw07hs0c",
                                "resource": {
                                    "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c/full/600,/0/default.jpg",
                                    "@type": "dctypes:Image",
                                    "format": "image/jpeg",
                                    "service": {
                                        "@context": "http://iiif.io/api/image/2/context.json",
                                        "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c",
                                        "profile": "http://iiif.io/api/image/2/level0.json",
                                    },
                                },
                            }
                        ],
                    },
                    {
                        "@type": "sc:Canvas",
                        "label": "f. 049v",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/dw84c98r",
                        "width": 5332,
                        "height": 7008,
                        "images": [
                            {
                                "@type": "oa:Annotation",
                                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/annotation/dw84c98r",
                                "motivation": "sc:painting",
                                "on": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/dw84c98r",
                                "resource": {
                                    "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fdw84c98r/full/600,/0/default.jpg",
                                    "@type": "dctypes:Image",
                                    "format": "image/jpeg",
                                    "service": {
                                        "@context": "http://iiif.io/api/image/2/context.json",
                                        "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fdw84c98r",
                                        "profile": "http://iiif.io/api/image/2/level0.json",
                                    },
                                },
                            }
                        ],
                    },
                ],
            }
        ],
    },
)

MANIFEST_WITHOUT_F001R = MockResponse(
    200,
    {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "label": "Sinai Arabic 352. Mimars and Lives of Saints : manuscript, 1200. St. Catherine's Monastery, Sinai, Egypt",
        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest",
        "@type": "sc:Manifest",
        "sequences": [
            {
                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/sequence/normal",
                "@type": "sc:Sequence",
                "canvases": [
                    {
                        "@type": "sc:Canvas",
                        "label": "Front Board Outside",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/hm957748",
                        "width": 5332,
                        "height": 7006,
                        "images": [
                            {
                                "@type": "oa:Annotation",
                                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/annotation/hm957748",
                                "motivation": "sc:painting",
                                "on": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/hm957748",
                                "resource": {
                                    "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fhm957748/full/600,/0/default.jpg",
                                    "@type": "dctypes:Image",
                                    "format": "image/jpeg",
                                    "service": {
                                        "@context": "http://iiif.io/api/image/2/context.json",
                                        "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fhm957748",
                                        "profile": "http://iiif.io/api/image/2/level0.json",
                                    },
                                },
                            }
                        ],
                    },
                    {
                        "@type": "sc:Canvas",
                        "label": "f. 001v",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/zw07hs0c",
                        "width": 5332,
                        "height": 7008,
                        "images": [
                            {
                                "@type": "oa:Annotation",
                                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/annotation/zw07hs0c",
                                "motivation": "sc:painting",
                                "on": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/zw07hs0c",
                                "resource": {
                                    "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c/full/600,/0/default.jpg",
                                    "@type": "dctypes:Image",
                                    "format": "image/jpeg",
                                    "service": {
                                        "@context": "http://iiif.io/api/image/2/context.json",
                                        "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c",
                                        "profile": "http://iiif.io/api/image/2/level0.json",
                                    },
                                },
                            }
                        ],
                    },
                    {
                        "@type": "sc:Canvas",
                        "label": "f. 049v",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/dw84c98r",
                        "width": 5332,
                        "height": 7008,
                        "images": [
                            {
                                "@type": "oa:Annotation",
                                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/annotation/dw84c98r",
                                "motivation": "sc:painting",
                                "on": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/dw84c98r",
                                "resource": {
                                    "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fdw84c98r/full/600,/0/default.jpg",
                                    "@type": "dctypes:Image",
                                    "format": "image/jpeg",
                                    "service": {
                                        "@context": "http://iiif.io/api/image/2/context.json",
                                        "@id": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fdw84c98r",
                                        "profile": "http://iiif.io/api/image/2/level0.json",
                                    },
                                },
                            }
                        ],
                    },
                ],
            }
        ],
    },
)

MANIFEST_WITHOUT_IMAGES = MockResponse(
    200,
    {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "label": "Sinai Arabic 352. Mimars and Lives of Saints : manuscript, 1200. St. Catherine's Monastery, Sinai, Egypt",
        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest",
        "@type": "sc:Manifest",
        "sequences": [
            {
                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/sequence/normal",
                "@type": "sc:Sequence",
                "canvases": [
                    {
                        "@type": "sc:Canvas",
                        "label": "Front Board Outside",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/hm957748",
                        "width": 5332,
                        "height": 7006,
                        "images": [],
                    },
                ],
            }
        ],
    },
)

BAD_MANIFEST = MockResponse(
    200,
    {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "label": "Sinai Arabic 352. Mimars and Lives of Saints : manuscript, 1200. St. Catherine's Monastery, Sinai, Egypt",
        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest",
        "@type": "sc:Manifest",
        "json_mistake": [
            {
                "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/sequence/normal",
                "@type": "sc:Sequence",
                "canvases": [
                    {
                        "@type": "sc:Canvas",
                        "label": "Front Board Outside",
                        "@id": "http://test-iiif.library.ucla.edu/ark%3A%2F21198%2Fz14b44n8/manifest/canvas/hm957748",
                        "width": 5332,
                        "height": 7006,
                        "images": [],
                    },
                ],
            }
        ],
    },
)
