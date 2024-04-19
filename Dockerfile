FROM codemodder/pixee-cli:0.0.1
COPY . /pixee/ci-integrations
WORKDIR /pixee/ci-integrations
RUN pip install -e /pixee/ci-integrations

#ENTRYPOINT ["python", "/pixee/ci-integrations/main.py"]
ENTRYPOINT ["bash", "run.sh"]