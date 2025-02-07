import launchflow as lf

min_instance = 2
max_instance = 4
machine_type_redis = "e2-small"
machine_type_postgres = "e2-medium"
domain_name = "docs.smartdocsealth.com"

SECRET_KEY = lf.gcp.SecretManagerSecret("secret-key")
SSO_TOKEN = lf.gcp.SecretManagerSecret("sso-token")
OPENAI_API_KEY = lf.gcp.SecretManagerSecret("openai-api-key")

ENVIRONMENT = "prod"

if lf.environment == "dev":
    min_instance = 1
    max_instance = 2
    machine_type_redis = "e2-micro"
    machine_type_postgres = "e2-micro"
    domain_name = f"{'dev.'}docs.smartdocsealth.com"
    ENVIRONMENT = "dev"

if lf.environment == "stage":
    domain_name = f"{'stage.'}docs.smartdocsealth.com"
    ENVIRONMENT = "stage"
    min_instance = 1
    max_instance = 3

# db-n1-standard-1 == 1 vCPU + 3840MB RAM
# db-g1-small == shared vCPU + 1.7GB RAM, $33.434/month
postgres = lf.gcp.ComputeEnginePostgres(
    f"django-postgres-{lf.environment}", machine_type=machine_type_postgres
)

redis = lf.gcp.ComputeEngineRedis(
    f"django-backend-redis-{lf.environment}",
    machine_type=machine_type_redis,
)

storage = lf.gcp.GCSBucket(
    f"docs-backend-storage-{lf.environment}",
    uniform_bucket_level_access=True,
    force_destroy=True,
)

environment_variables = {}

# wrapped in try/catch to avoid error during first run
try:
    environment_variables = {
        "SECRET_KEY": SECRET_KEY.version().decode(),
        "SSO_TOKEN": SSO_TOKEN.version().decode(),
        "OPENAI_API_KEY": OPENAI_API_KEY.version().decode(),
        "ENVIRONMENT": ENVIRONMENT,
    }

except Exception as e:
    print(f"Error: {e}")

backend = lf.gcp.CloudRun(
    f"django-backend-service",
    dockerfile="Dockerfile.launchflow",
    build_ignore=[
        ".venv/",
        ".terraform/",
        ".vscode/",
    ],
    memory="1024Mi",
    domain=domain_name,
    min_instance_count=min_instance,
    max_instance_count=max_instance,
    environment_variables=environment_variables,
)
