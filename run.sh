docker build -t stebo85/qsmxt:210818 -f qsm.Dockerfile .

rm -rf analysis_output
mkdir analysis_output

python test_tool.py stebo85/qsmxt:210818 example_data analysis_output \
    --settings settings.json \
    --values mock_settings_values.json