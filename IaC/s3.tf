
resource "aws_s3_bucket" "mmu_db_migration" {
  bucket = "mmu-library-sql-migration"

  tags = {
    Name        = "mmu-library-sql-migration"
    Purpose     = "database-migration"
    Environment = "academic"
  }
}

resource "aws_s3_bucket_public_access_block" "mmu_db_migration_block" {
  bucket = aws_s3_bucket.mmu_db_migration.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "mmu_db_migration_ownership" {
  bucket = aws_s3_bucket.mmu_db_migration.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "mmu_db_migration_versioning" {
  bucket = aws_s3_bucket.mmu_db_migration.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mmu_db_migration_encryption" {
  bucket = aws_s3_bucket.mmu_db_migration.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_object" "db_migration_folder" {
  bucket  = aws_s3_bucket.mmu_db_migration.id
  key     = "db-migration/"
  content = ""
}

resource "aws_s3_object" "migration_sql" {
  bucket = aws_s3_bucket.mmu_db_migration.id
  key    = "db-migration/complete_sql.sql"
  source = "complete_sql.sql"
  etag   = filemd5("complete_sql.sql")
}
