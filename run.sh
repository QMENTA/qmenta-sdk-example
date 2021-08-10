rm -rf analysis_output
mkdir analysis_output

python test_tool.py stebo85/qmentatest:210810 example_data analysis_output \
    --settings settings.json \
    --values mock_settings_values.json