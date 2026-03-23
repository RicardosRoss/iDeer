#!/bin/bash

cd /var/www/daily-recommender

/root/miniconda3/bin/python main.py \
    --sources github huggingface \
    --provider OpenAI --model gpt-5.2 \
    --base_url https://api.boyuerichdata.opensphereai.com/v1 \
    --api_key sk-1XupAEf1erN0qBAuT1cYFeKnQiKrU1AdX0S4tj7uha3Fwfqg \
    --smtp_server smtp.qq.com --smtp_port 465 \
    --sender 1274006768@qq.com --receiver liyu@pjlab.org.cn \
    --sender_password fazhygeajrgeggec \
    --num_workers 8 \
    --temperature 0.5 \
    --description description.txt \
    --save \
    --generate_ideas \
    --researcher_profile researcher_profile.md \
    --gh_languages all --gh_since daily --gh_max_repos 30 \
    --hf_content_type papers models --hf_max_papers 30 --hf_max_models 15
