"""Tests for the text reuse module."""

import logging
from unittest import TestCase, skip

import spacy
from dphon.reuse import MatchGraph
from spacy.tokens import Doc
from dphon.extend import LevenshteinExtender
from dphon.match import Match

# disconnect logging for testing
logging.captureWarnings(True)
logging.disable(logging.CRITICAL)


class TestMatchGraph(TestCase):
    """Test the MatchGraph class."""

    maxDiff = None

    def setUp(self) -> None:
        """create a spaCy pipeline and match graph for testing"""
        self.nlp = spacy.blank(
            "zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
        self.G = MatchGraph()
        if not Doc.has_extension("id"):
            Doc.set_extension("id", default="")
        # doc1 = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        # doc2 = self.nlp.make_doc("與朋友交言而有信雖曰已學吾必謂之未也")
        # doc3 = self.nlp.make_doc("與朋友交言而有信雖未讀書吾亦謂之學矣")

    def test_extend(self) -> None:
        """extend should reduce graph to maximal matches only"""
        doc1 = self.nlp.make_doc("與朋友交言而有信雖曰未學吾")
        doc2 = self.nlp.make_doc("與朋友交言而有信雖曰已學吾")
        doc3 = self.nlp.make_doc("與朋友交言而有信雖未讀書吾")
        self.G.add_docs([("論語·學而", doc1),
                         ("藝文類聚·錢", doc2),
                         ("顏氏家訓·勉學", doc3)])
        self.G.add_matches([
            Match("論語·學而", "藝文類聚·錢", doc1[0:4], doc2[0:4]),      # 與朋友交
            Match("論語·學而", "藝文類聚·錢", doc1[4:8], doc2[4:8]),      # 言而有信
            Match("論語·學而", "顏氏家訓·勉學", doc1[0:4], doc3[0:4]),    # 與朋友交
            Match("論語·學而", "顏氏家訓·勉學", doc1[4:8], doc3[4:8]),    # 言而有信
            Match("藝文類聚·錢", "顏氏家訓·勉學", doc2[0:4], doc3[0:4]),  # 與朋友交
            Match("藝文類聚·錢", "顏氏家訓·勉學", doc2[4:8], doc3[4:8]),  # 言而有信
        ])
        extender = LevenshteinExtender(threshold=0.8, len_limit=50)
        self.G.extend(extender)
        matches = [(m.u, m.v, m.utxt.text, m.vtxt.text)
                   for m in self.G.matches]
        self.assertEqual(len(matches), 3)
        self.assertEqual(matches[0], ("論語·學而", "藝文類聚·錢",
                                      "與朋友交言而有信雖曰未學吾", "與朋友交言而有信雖曰已學吾"))
        self.assertEqual(matches[1], ("論語·學而", "顏氏家訓·勉學",
                                      "與朋友交言而有信雖曰未學吾", "與朋友交言而有信雖未讀書吾"))
        self.assertEqual(matches[2], ("藝文類聚·錢", "顏氏家訓·勉學",
                                      "與朋友交言而有信雖", "與朋友交言而有信雖"))
