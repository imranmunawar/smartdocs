from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from io import BytesIO
from google.cloud import storage


class GCS_Client:
    """
    Class to perform GCS related tasks
    """

    def __init__(self):

        self.base_folder = settings.GCS_ENV_FOLDER
        self.bucket_name = settings.GS_BUCKET_NAME
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
    

    def upload_template_file_to_gcs(self, file: BytesIO, file_name: str) -> str:
        """
        Uploads a template docx file to GCS

        :param file: File to upload
        :type file: BytesIO
        :param file_name: Name of the file to upload as
        :type file_name: str
        :return: Path of the file if upload is success
        :rtype: str
        """

        key = f'{self.base_folder}/templates/{file_name}'

        try:
            # Create a ContentFile object with bytes content
            content_file = ContentFile(file.read())
            
            # Save the file using default_storage
            file_path = default_storage.save(key, content_file)

            # Check if the file was uploaded successfully
            blob = self.bucket.blob(key)
            if not blob.exists():
                raise ValueError("Uploaded file is empty")
            
            return file_path
        
        except Exception as e:
            print(f"Error uploading file to GCS: {e}")
            return None


    def read_document_from_gcs(self, file_name: str) -> BytesIO:
        """
        Gets a document from GCS

        :param file_name: File to retrieve
        :type file_name: str
        :return: File from GCS otherwise none
        :rtype: BytesIO
        """

        key = f'{self.base_folder}/templates/{file_name}'

        try:
            blob = self.bucket.blob(key)
            content = blob.download_as_bytes()
            return BytesIO(content)

        except Exception as e:
            print(f"Error reading file from GCS: {e}")
            return None
        

    def remove_template_file_from_gcs(self, file_name: str) -> bool:
        """
        Removes a template file from GCS

        :param file_name: Name of the file to remove
        :type file_name: str
        :return: If the removal was success
        :rtype: bool
        """

        key = f'{self.base_folder}/templates/{file_name}'

        try:
            blob = self.bucket.blob(key)
            blob.delete()
            return True

        except Exception as e:
            print(f"Error deleting file from GCS: {e}")
            return False


    def update_template_file_in_gcs(self, file:BytesIO, file_name:str) -> bool:
        """
        Updates a template docx file in s3

        :param file: File to update with
        :type file: BytesIO
        :param file_name: Name of the file to update
        :type file_name: str
        :return: File path if update was success else None
        :rtype: str
        """

        if not self.remove_template_file_from_gcs(file_name):
            print("Removal from s3 Failed while document update or file may not exist....")
        
        return self.upload_template_file_to_gcs(file, file_name)
    

    def upload_image_file_to_gcs(self, file: BytesIO, file_name: str) -> str:
        """
        Uploads an image file to GCS

        :param file: File to upload
        :type file: BytesIO
        :param file_name: Name of the file to upload as
        :type file_name: str
        :return: Path of the file if upload is success
        :rtype: str
        """

        key = f'{self.base_folder}/images/{file_name}'

        try:
            # Create a ContentFile object with bytes content
            content_file = ContentFile(file.read())
            
            # Save the file using default_storage
            file_path = default_storage.save(key, content_file)
            
            return file_path
        
        except Exception as e:
            print(f"Error uploading file to GCS: {e}")
            return None
        

    def download_image_from_gcs(self, file_name: str) -> BytesIO:
        """
        Gets an image from GCS

        :param file_name: File to retrieve
        :type file_name: str
        :return: File from GCS otherwise none
        :rtype: BytesIO
        """

        key = f'{self.base_folder}/images/{file_name}'

        try:
            blob = self.bucket.blob(key)
            content = blob.download_as_bytes()
            return BytesIO(content)
        except Exception as e:
            print(f"Error downloading image from GCS: {e}")
            return None
        

    def remove_image_from_gcs(self, file_name: str) -> bool:
        """
        Removes an image file from GCS

        :param file_name: Name of the file to remove
        :type file_name: str
        :return: If the removal was success
        :rtype: bool
        """

        key = f'{self.base_folder}/images/{file_name}'

        try:
            blob = self.bucket.blob(key)
            blob.delete()
            return True

        except Exception as e:
            print(f"Error deleting image from GCS: {e}")
            return False
