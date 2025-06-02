from google.cloud import storage
import os

def subir_a_gcp(nombre_local, bucket_name, nombre_remoto, credenciales_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credenciales_path

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(nombre_remoto)

    blob.upload_from_filename(nombre_local)
    print(f"☁️ Subido a GCP: {nombre_remoto}")
