# Gunakan image dasar Python
FROM python:3.10.0
# RUN pip install --upgrade pip

# Set direktori kerja
WORKDIR /app

# ENV PORT 1234

# Salin file requirements.txt dan install dependensi
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file proyek ke container
COPY . .

# Download NLTK datasets
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Expose port yang digunakan oleh aplikasi FastAPI
# EXPOSE 8080

# Perintah untuk menjalankan aplikasi
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
CMD exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
# CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 8
