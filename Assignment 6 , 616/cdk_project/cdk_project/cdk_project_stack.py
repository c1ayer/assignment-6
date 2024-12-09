from aws_cdk import (
    App,
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    Duration,
)
from constructs import Construct


class CdkProjectStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Parameters
        instance_type = "t2.micro"
        your_ip = "24.118.31.102/32"

        # VPC Configuration
        vpc = ec2.Vpc(
            self, "EngineeringVpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/18"),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # Key Pair
        key_name = "assignment6"  # Key pair created on AWS

        # Security Group
        sg = ec2.SecurityGroup(
            self, "WebserversSG",
            vpc=vpc,
            description="Security group for web servers",
            allow_all_outbound=True
        )
        sg.add_ingress_rule(ec2.Peer.ipv4(your_ip), ec2.Port.tcp(22), "Allow SSH")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")

        # IAM Role for EC2 instances to access S3
        role = iam.Role(
            self, "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")]
        )

        # Instances (Webserver1 and Webserver2)
        ami_id = "ami-01cc34ab2709337aa"  # Ensure this AMI is valid for your region

        webserver1 = ec2.Instance(
            self, "Webserver1",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=ec2.MachineImage.generic_linux({self.region: ami_id}),
            vpc=vpc,
            key_name=key_name,  # Use the existing key pair name here
            security_group=sg,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            user_data=ec2.UserData.custom(
                """#!/bin/bash
                yum update -y
                yum install -y git httpd php
                service httpd start
                chkconfig httpd on
                aws s3 cp s3://seis665-public/index.php /var/www/html/
                """
            ),
            role=role  # Attach the IAM role to the instance
        )

        webserver2 = ec2.Instance(
            self, "Webserver2",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=ec2.MachineImage.generic_linux({self.region: ami_id}),
            vpc=vpc,
            key_name=key_name,  # Use the existing key pair name here
            security_group=sg,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            user_data=ec2.UserData.custom(
                """#!/bin/bash
                yum update -y
                yum install -y git httpd php
                service httpd start
                chkconfig httpd on
                aws s3 cp s3://seis665-public/index.php /var/www/html/
                """
            ),
            role=role  # Attach the IAM role to the instance
        )

        # Application Load Balancer
        lb = elbv2.ApplicationLoadBalancer(
            self, "EngineeringLB",
            vpc=vpc,
            internet_facing=True,
            security_group=sg
        )

        listener = lb.add_listener(
            "Listener",
            port=80,
            open=True
        )

        # Target Group
        target_group = elbv2.ApplicationTargetGroup(
            self, "TargetGroup",
            vpc=vpc,
            protocol=elbv2.ApplicationProtocol.HTTP,
            port=80,
            health_check=elbv2.HealthCheck(
                path="/",
                port="80",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                healthy_threshold_count=5,
                unhealthy_threshold_count=2
            )
        )

        target_group.add_target(webserver1)
        target_group.add_target(webserver2)

        listener.add_target_groups(
            "AddTargetGroup",
            target_groups=[target_group]
        )

        # Output: Load Balancer DNS Name
        self.output = self.add_output(
            "LoadBalancerDNSName",
            value=lb.load_balancer_dns_name,
            description="DNS Name of the load balancer"
        )


# App initialization and stack deployment
app = App()
CdkProjectStack(app, "CdkProjectStack")
app.synth()
