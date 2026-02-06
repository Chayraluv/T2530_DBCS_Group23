MMU LIBRARY CLOUD INFRASTRUCTURE
Infrastructure as Code (IaC) – Terraform

PROJECT OVERVIEW
This project documents the cloud infrastructure for the MMU Library Web System using Infrastructure as Code (IaC) with Terraform. All AWS resources created in the AWS Management Console are fully represented in Terraform configuration files.

The infrastructure follows cloud best practices, including network segmentation, least-privilege security, load balancing, and private database deployment.

--------------------------------------------------

ARCHITECTURE SUMMARY
- VPC with CIDR 10.0.0.0/16
- Public subnets for ALB and EC2
- Private subnets for application and database
- Internet-facing Application Load Balancer (ALB)
- EC2 web server running application on port 5000
- Aurora MySQL database deployed in private subnets
- Amazon S3 bucket for database migration files

Traffic Flow:
Internet → ALB (HTTP:80)
         → EC2 Web Server (App:5000)
         → Aurora MySQL (Private:3306)

--------------------------------------------------

SECURITY DESIGN
- Only HTTP port 80 is publicly accessible via ALB
- Application port 5000 is restricted to ALB traffic only
- Database port 3306 is restricted to EC2 security group
- SSH access limited to administrator IP
- S3 bucket:
  - Public access fully blocked
  - Bucket owner enforced
  - Server-side encryption enabled (AES-256)

External validation using Nmap confirms:
- Port 80: OPEN
- Port 443: CLOSED

--------------------------------------------------

INFRASTRUCTURE AS CODE
All infrastructure components are defined using Terraform:
- VPC, subnets, route tables, and internet gateway
- Security groups
- EC2 instance
- Application Load Balancer, target group, and listener
- Aurora MySQL cluster
- Amazon S3 bucket with security configuration

The IaC files are provided for academic documentation purposes.
Executing terraform apply is not required for submission.

--------------------------------------------------

REPOSITORY STRUCTURE

IaC/
- provider.tf
- variables.tf
- vpc.tf
- subnets.tf
- igw.tf
- route_tables.tf
- security_groups.tf
- ec2.tf
- alb.tf
- target_group.tf
- listener.tf
- rds.tf
- s3.tf
- outputs.tf

--------------------------------------------------

DATABASE MIGRATION (S3)
An Amazon S3 bucket is used to store database migration scripts.
- Bucket name: mmu-library-sql-migration
- Folder: db-migration/
- File: complete_sql.sql
- Encryption enabled
- Public access blocked

--------------------------------------------------

CONCLUSION
This project demonstrates a complete, secure, and production-style AWS cloud infrastructure implemented using Infrastructure as Code. All deployed resources are fully documented in Terraform, fulfilling academic and technical requirements.

--------------------------------------------------

Author:
Nur Adibah
Bachelor of Computer Science (Data Science)
Multimedia University (MMU)
