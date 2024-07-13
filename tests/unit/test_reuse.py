"""Tests for the text reuse module."""

import logging
from unittest import TestCase, skip

import spacy
from spacy.tokens import Doc

from dphon.extend import LevenshteinExtender
from dphon.match import Match
from dphon.reuse import MatchGraph

# disconnect logging for testing
logging.captureWarnings(True)
logging.disable(logging.CRITICAL)


class TestMatchGraph(TestCase):
    """Test the MatchGraph class."""

    maxDiff = None

    def setUp(self) -> None:
        """create a spaCy pipeline and match graph for testing"""
        self.nlp = spacy.blank(
            "zh", meta={"tokenizer": {"config": {"use_jieba": False}}}
        )
        if not Doc.has_extension("id"):
            Doc.set_extension("id", default="")
        if not Doc.has_extension("groups"):
            Doc.set_extension("groups", default=[])

    def test_extend(self) -> None:
        """extend should reduce graph to maximal matches only"""
        doc1 = self.nlp.make_doc("與朋友交言而有信雖曰未學吾")
        doc2 = self.nlp.make_doc("與朋友交言而有信雖曰已學吾")
        doc3 = self.nlp.make_doc("與朋友交言而有信雖未讀書吾")
        doc1._.id = "論語·學而"
        doc2._.id = "藝文類聚·錢"
        doc3._.id = "顏氏家訓·勉學"
        G = MatchGraph()
        G.add_docs([doc1, doc2, doc3])
        G.add_matches(
            [
                Match("論語·學而", "藝文類聚·錢", doc1[0:4], doc2[0:4]),  # 與朋友交
                Match("論語·學而", "藝文類聚·錢", doc1[4:8], doc2[4:8]),  # 言而有信
                Match("論語·學而", "顏氏家訓·勉學", doc1[0:4], doc3[0:4]),  # 與朋友交
                Match("論語·學而", "顏氏家訓·勉學", doc1[4:8], doc3[4:8]),  # 言而有信
                Match("藝文類聚·錢", "顏氏家訓·勉學", doc2[0:4], doc3[0:4]),  # 與朋友交
                Match("藝文類聚·錢", "顏氏家訓·勉學", doc2[4:8], doc3[4:8]),  # 言而有信
            ]
        )
        extender = LevenshteinExtender(threshold=0.8, len_limit=50)
        G.extend(extender)
        matches = [(m.u, m.v, m.utxt.text, m.vtxt.text) for m in G.matches]
        self.assertEqual(len(matches), 3, "should have 3 matches")
        self.assertEqual(
            matches[0],
            (
                "論語·學而",
                "藝文類聚·錢",
                "與朋友交言而有信雖曰未學吾",
                "與朋友交言而有信雖曰已學吾",
            ),
        )
        self.assertEqual(
            matches[1],
            (
                "論語·學而",
                "顏氏家訓·勉學",
                "與朋友交言而有信雖曰未學吾",
                "與朋友交言而有信雖未讀書吾",
            ),
        )
        self.assertEqual(
            matches[2],
            (
                "藝文類聚·錢",
                "顏氏家訓·勉學",
                "與朋友交言而有信雖",
                "與朋友交言而有信雖",
            ),
        )

    def test_filter(self) -> None:
        """filter should remove matches that don't meet a predicate"""
        doc1 = self.nlp.make_doc("abcdefg123")
        doc2 = self.nlp.make_doc("abcdefg456")
        doc3 = self.nlp.make_doc("456nothing")
        doc1._.id = "1"
        doc2._.id = "2"
        doc3._.id = "3"
        G = MatchGraph()
        G.add_docs([doc1, doc2, doc3])
        G.add_matches(
            [
                Match("1", "2", doc1[0:7], doc2[0:7]),  # abcdefg
                Match("2", "3", doc2[7:10], doc3[3:6]),  # 456
            ]
        )
        G.filter(lambda m: len(m) > 3)
        self.assertEqual(G.number_of_matches, 1, "should have 1 match with length > 3")
        match_texts = [m.utxt.text for m in G.matches]
        self.assertEqual(match_texts[0], "abcdefg")

    def test_group(self) -> None:
        """grouping should group matches by shared spans"""
        doc1 = self.nlp.make_doc("與朋友交言而有信雖曰未學吾")
        doc2 = self.nlp.make_doc("與朋友交言而有信雖曰已學吾")
        doc3 = self.nlp.make_doc("與朋友交言而有信雖未讀書吾")
        doc1._.id = "論語·學而"
        doc2._.id = "藝文類聚·錢"
        doc3._.id = "顏氏家訓·勉學"
        G = MatchGraph()
        G.add_docs([doc1, doc2, doc3])
        G.add_matches(
            [
                Match(
                    "論語·學而", "藝文類聚·錢", doc1[0:8], doc2[0:8]
                ),  # 與朋友交言而有信
                Match(
                    "論語·學而", "顏氏家訓·勉學", doc1[0:8], doc3[0:8]
                ),  # 與朋友交言而有信
                Match(
                    "藝文類聚·錢", "顏氏家訓·勉學", doc2[0:8], doc3[0:8]
                ),  # 與朋友交言而有信
            ]
        )
        G.group()
        self.assertEqual(len(doc1._.groups), 1)
        self.assertEqual(len(doc2._.groups), 1)
        self.assertEqual(len(doc3._.groups), 1)
        group = doc1._.groups[0]
        self.assertEqual(group.start, 0)
        self.assertEqual(group.end, 8)
        self.assertEqual(len(group), 2)
