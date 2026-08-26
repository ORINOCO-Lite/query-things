import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from query_things.filter_links_pid import cli


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_record():
    """Provide a sample JSON record."""
    return {
        'pid': 'rec1',
        'title': 'Test Record',
        'related_to': {'object': 'pid123'},
        'tags': ['tag1', 'tag2'],
    }


@pytest.fixture
def sample_record_multiple_links():
    """Provide a record with multiple link properties."""
    return {
        'pid': 'rec2',
        'title': 'Complex Record',
        'related_to': {'object': 'pid123'},
        'linked_from': ['pid456', 'pid789'],
    }


class TestFilterLinksPidBasic:
    """Basic tests for filter-links-pid command."""

    def test_command_requires_link_option(self, runner):
        """Test that --link option is required."""
        result = runner.invoke(cli, [])
        assert result.exit_code != 0
        assert 'required' in result.output.lower() or 'error' in result.output.lower()

    def test_single_link_filter_match(self, runner, sample_record):
        """Test filtering a record that matches the link criteria."""
        input_data = json.dumps(sample_record)

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'related_to',
                    'pid123',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0
        assert input_data in result.output

    def test_single_link_filter_no_match(self, runner, sample_record):
        """Test filtering a record that doesn't match the link criteria."""
        input_data = json.dumps(sample_record)

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'related_to',
                    'pid999',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0
        assert input_data not in result.output

    def test_multiple_records(self, runner):
        """Test filtering multiple JSON records from stdin."""
        record1 = {'pid': 'rec1', 'links_to': {'object': 'pid123'}}
        record2 = {'pid': 'rec2', 'links_to': {'object': 'pid456'}}
        input_data = f'{json.dumps(record1)}\n{json.dumps(record2)}\n'

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'links_to',
                    'pid123',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0
        assert json.dumps(record1) in result.output
        assert json.dumps(record2) not in result.output

    def test_multiple_link_filters(self, runner):
        """Test filtering with multiple --link criteria (AND logic)."""
        record = {
            'pid': 'rec1',
            'related_to': {'object': 'pid123'},
            'linked_from': {'object': 'pid456'},
        }
        input_data = json.dumps(record)

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'related_to',
                    'pid123',
                    '--link',
                    'linked_from',
                    'pid456',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0
        assert input_data in result.output

    def test_list_property_matching(self, runner):
        """Test matching against list properties."""
        record = {'pid': 'rec1', 'tags': ['tag1', 'pid123', 'tag3']}
        input_data = json.dumps(record)

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'tags',
                    'pid123',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0
        assert input_data in result.output

    def test_recursive_flag(self, runner, sample_record):
        """Test that recursive flag is accepted."""
        input_data = json.dumps(sample_record)

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'related_to',
                    'pid123',
                    '--recursive',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0

    def test_collection_option(self, runner, sample_record):
        """Test specifying custom collection."""
        input_data = json.dumps(sample_record)

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'related_to',
                    'pid123',
                    '--collection',
                    'custom_collection',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0

    def test_missing_link_property(self, runner):
        """Test record without the specified link property."""
        record = {'pid': 'rec1', 'title': 'No links'}
        input_data = json.dumps(record)

        with patch('query_things.common.api._get_rec_from_any_collection'):
            result = runner.invoke(
                cli,
                [
                    '--link',
                    'nonexistent_property',
                    'pid123',
                    '--api-url',
                    'http://test.api',
                ],
                input=input_data,
            )

        assert result.exit_code == 0
        assert input_data not in result.output
