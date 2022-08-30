from aws_cdk.aws_ec2 import RouterType, CfnSecurityGroup
from aws_cdk import CfnTag

# basic VPC configs
VPC = 'ecs-stack-vpc'
VPC_CIDR = "10.0.0.0/16"
INTERNET_GATEWAY = 'ecs-stack-igw'
REGION = 'us-east-1'

# route tables
PUBLIC_ROUTE_TABLE = 'ecs-stack-public-rtb'
PRIVATE_ROUTE_TABLE = 'ecs-stack-private-rtb'

ROUTE_TABLES_ID_TO_ROUTES_MAP = {
    PUBLIC_ROUTE_TABLE: [
        {
            'destination_cidr_block': '0.0.0.0/0',
            'gateway_id': INTERNET_GATEWAY,
            'router_type': RouterType.GATEWAY
        }
    ],
    PRIVATE_ROUTE_TABLE: [
    ]
}

# security groups
SECURITY_GROUP = 'ecs-stack-sg'

SECURITY_GROUP_ID_TO_CONFIG = {
    SECURITY_GROUP: {
        'group_description': 'SG of the ecs servers',
        'group_name': SECURITY_GROUP,
        'security_group_ingress': [
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=80, to_port=80
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=80, to_port=80
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=443, to_port=443
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=443, to_port=443
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=22, to_port=22
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=22, to_port=22
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=5000, to_port=5000
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=5000, to_port=5000
            ),
        ],
        'tags': [
            CfnTag(
                key='Name', value=SECURITY_GROUP
            )
        ]
    },
}

# subnets and instances
PUBLIC_SUBNET_01 = 'ecs-stack-public-sn-1'
PUBLIC_SUBNET_02 = 'ecs-stack-public-sn-2'
PRIVATE_SUBNET_01 = 'ecs-stack-private-sn-1'

SUBNET_CONFIGURATION = {
    PUBLIC_SUBNET_01: {
        'availability_zone': 'us-east-1a', 
        'cidr_block': '10.0.1.0/24', 
        'map_public_ip_on_launch': True,
        'route_table_id': PUBLIC_ROUTE_TABLE
    },
    PUBLIC_SUBNET_02: {
        'availability_zone': 'us-east-1b', 
        'cidr_block': '10.0.3.0/24', 
        'map_public_ip_on_launch': True,
        'route_table_id': PUBLIC_ROUTE_TABLE
    },
    PRIVATE_SUBNET_01: {
        'availability_zone': 'us-east-1c', 
        'cidr_block': '10.0.4.0/24', 
        'map_public_ip_on_launch': False,
        'route_table_id': PUBLIC_ROUTE_TABLE,
        # 'route_table_id': PRIVATE_ROUTE_TABLE,
    }
}