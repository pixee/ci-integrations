FROM codemodder/pixee-cli:0.0.2
COPY . /pixee/ci-integrations
WORKDIR /pixee/ci-integrations
RUN pip install -e /pixee/ci-integrations

ENV GITHUB_TOKEN=${GITHUB_TOKEN}

ENTRYPOINT ["python", "/pixee/ci-integrations/main.py"]
#ENTRYPOINT ["bash", "/pixee/ci-integrations/run.sh"]