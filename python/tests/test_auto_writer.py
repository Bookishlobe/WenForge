"""Tests for auto_writer module."""

import json
from auto_writer import AutoWriter, STYLE_DESCRIPTIONS, CHAPTER_LENGTHS


class TestAutoWriterInit:
    def test_init_stores_provider_and_model(self, mock_provider):
        writer = AutoWriter(mock_provider, "test-model")
        assert writer.provider is mock_provider
        assert writer.model == "test-model"


class TestGenerateOutline:
    def test_generate_outline_returns_dict(self, mock_provider, mock_config):
        mock_provider.generate.return_value.text = json.dumps({
            "title": "测试小说",
            "world_setting": "修仙世界",
            "characters": [],
            "chapter_outlines": ["第1章：开始", "第2章：发展"],
            "story_arcs": "主线故事",
        }, ensure_ascii=False)
        writer = AutoWriter(mock_provider, "test-model")
        result = writer.generate_outline({
            "genre": "玄幻",
            "premise": "一个少年修仙的故事",
            "protagonist": "小明",
            "style": "流畅直白",
            "total_chapters": 10,
            "chapter_length": "medium",
        })
        assert "title" in result
        assert "chapter_outlines" in result

    def test_generate_outline_fallback_on_bad_json(self, mock_provider, mock_config):
        mock_provider.generate.return_value.text = "invalid json{{{"
        writer = AutoWriter(mock_provider, "test-model")
        result = writer.generate_outline({
            "genre": "玄幻",
            "premise": "test",
            "protagonist": "小明",
            "style": "流畅直白",
            "total_chapters": 5,
            "chapter_length": "medium",
        })
        assert len(result["chapter_outlines"]) == 5

    def test_outline_pads_chapters(self, mock_provider, mock_config):
        mock_provider.generate.return_value.text = json.dumps({
            "title": "测试",
            "world_setting": "世界",
            "characters": [],
            "chapter_outlines": ["第1章"],
            "story_arcs": "",
        })
        writer = AutoWriter(mock_provider, "test-model")
        result = writer.generate_outline({
            "genre": "玄幻", "premise": "t", "protagonist": "p",
            "style": "流畅直白", "total_chapters": 10, "chapter_length": "medium",
        })
        assert len(result["chapter_outlines"]) == 10


class TestGenerateChapter:
    def test_generate_chapter_returns_text(self, mock_provider, mock_config, sample_outline):
        writer = AutoWriter(mock_provider, "test-model")
        text = writer.generate_chapter(
            outline=sample_outline,
            index=1,
            chapter_outline="第1章：开始",
            prev_summaries=[],
            config={"style": "流畅直白", "chapter_length": "medium"},
        )
        assert isinstance(text, str)
        assert len(text) > 0

    def test_generate_chapter_with_summaries(self, mock_provider, mock_config, sample_outline):
        writer = AutoWriter(mock_provider, "test-model")
        text = writer.generate_chapter(
            outline=sample_outline,
            index=2,
            chapter_outline="第2章：发展",
            prev_summaries=["第1章内容概要..."],
            config={"style": "流畅直白", "chapter_length": "short"},
        )
        assert isinstance(text, str)

    def test_chapter_length_constants(self):
        assert CHAPTER_LENGTHS["short"] == 2000
        assert CHAPTER_LENGTHS["medium"] == 3000
        assert CHAPTER_LENGTHS["long"] == 5000


class TestStyleDescriptions:
    def test_all_styles_have_descriptions(self):
        assert len(STYLE_DESCRIPTIONS) == 6
        assert "流畅直白" in STYLE_DESCRIPTIONS
        assert "古风典雅" in STYLE_DESCRIPTIONS


class TestParseJson:
    def test_parse_plain_json(self, mock_provider, mock_config):
        writer = AutoWriter(mock_provider, "m")
        result = writer._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_markdown_fence(self, mock_provider, mock_config):
        writer = AutoWriter(mock_provider, "m")
        result = writer._parse_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}


class TestPadChapters:
    def test_pad_does_not_exceed_target(self, mock_provider):
        writer = AutoWriter(mock_provider, "m")
        result = writer._pad_chapters(["a", "b", "c"], 5)
        assert len(result) == 5

    def test_pad_truncates_if_over(self, mock_provider):
        writer = AutoWriter(mock_provider, "m")
        result = writer._pad_chapters(["a", "b", "c", "d", "e"], 3)
        assert len(result) == 3
