import boto3
from django.conf import settings
from io import BytesIO

class S3_Client():
    """
    Class to perform s3 Related tasks
    """

    def __init__(self):

        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.base_folder = settings.AWS_S3_ENV_FOLDER
        
    
    def upload_template_file_to_s3(self, file:BytesIO, file_name:str) -> str:
        """
        Uploads a template docx file to s3

        :param file: File to upload
        :type file: BytesIO
        :param file_name: Name of the file to upload as
        :type file_name: str
        :return: Path of the file if upload is success
        :rtype: str
        """

        key = f'{self.base_folder}/templates/{file_name}'

        try:
            self.s3.upload_fileobj(file, self.bucket_name, key)

            response = self.s3.head_object(Bucket=self.bucket_name, Key=key)
            if response['ContentLength'] == 0:
                self.s3.delete_object(Bucket=self.bucket_name, Key=key)
                raise ValueError("Uploaded file is empty")
            
            return key
        
        except Exception as e:
            print(f"Error uploading file to S3: {e}")
            return None


    def remove_template_file_from_s3(self, file_name:str) -> bool:
        """
        Removes a template file from s3

        :param file_name: Name of the file to remove
        :type file_name: str
        :return: If the removal was success
        :rtype: bool
        """

        key = f'{self.base_folder}/templates/{file_name}'

        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True

        except Exception as e:
            print(f"Error deleting file from S3: {e}")
            return False


    def update_template_file_in_s3(self, file:BytesIO, file_name:str) -> bool:
        """
        Updates a template docx file in s3

        :param file: File to update with
        :type file: BytesIO
        :param file_name: Name of the file to update
        :type file_name: str
        :return: If update was success
        :rtype: bool
        """

        if not self.remove_template_file_from_s3(file_name):
            print("Removal from s3 Failed while document update....")
            return None
        
        return self.upload_template_file_to_s3(file, file_name)

    
    def read_document_from_s3(self, file_name:str) -> BytesIO:
        """
        Gets a document from s3

        :param file_name: File to retrieve
        :type file_name: str
        :return: File from s3 otherwise none
        :rtype: BytesIO
        """

        key = f'{self.base_folder}/templates/{file_name}'

        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read()
            return BytesIO(content)

        except Exception as e:
            print(f"Error reading file from S3: {e}")
            return None

    
    def upload_image_file_to_s3(self, file, file_name:str) ->str:
        """
        Uploads a answer image file to s3

        :param file: File to upload
        :type file: BytesIO
        :param file_name: Name of the file to upload as
        :type file_name: str
        :return: Path of the file if upload is success
        :rtype: str
        """

        key = f'{self.base_folder}/images/{file_name}'

        try:
            self.s3.upload_fileobj(file, self.bucket_name, key)
            return key
        
        except Exception as e:
            print(f"Error uploading file to S3: {e}")
            return None


    def download_image_from_s3(self, file_name:str):
        """
        Gets a document from s3

        :param file_name: File to retrieve
        :type file_name: str
        :return: File from s3 otherwise none
        :rtype: File
        """

        key = f'{self.base_folder}/images/{file_name}'
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read()
            return content
        except Exception as e:
            print(f"Error downloading image from S3: {e}")
            return None

    def remove_image_from_s3(self, file_name:str) -> bool:
        """
        Removes a template file from s3

        :param file_name: Name of the file to remove
        :type file_name: str
        :return: If the removal was success
        :rtype: bool
        """

        key = f'{self.base_folder}/images/{file_name}'

        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True

        except Exception as e:
            print(f"Error deleting image from S3: {e}")
            return False