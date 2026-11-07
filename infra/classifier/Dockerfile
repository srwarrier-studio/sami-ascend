FROM python:3.14-slim
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir "laya[serve]"
ENV HF_HOME=/cache XDG_CACHE_HOME=/cache LAYA_HOST=0.0.0.0 LAYA_PORT=8011
EXPOSE 8011
CMD ["laya-serve"]
