from aws_cdk import (
    Stack,
    CfnTag,
    aws_ecs,
    CfnOutput
)
from aws_cdk.aws_ec2 import (
    Vpc, CfnInternetGateway, CfnVPCGatewayAttachment, CfnRouteTable,
    RouterType, CfnRoute, CfnSubnet, CfnSubnetRouteTableAssociation,
    CfnSecurityGroup
)
from constructs import Construct

from . import config

class EcsClusterTemplateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        
        # create VPC
        self.bifrost_vpc = Vpc(
            self,
            id=config.VPC, 
            cidr=config.VPC_CIDR, 
            nat_gateways=0, 
            subnet_configuration=[], 
            enable_dns_support=True,
            enable_dns_hostnames=True,
        )

        # some dictionaries
        self.subnet_id_to_subnet_map = {}
        self.route_table_id_to_route_table_map = {}
        self.security_group_id_to_group_map = {}
        
        # create internet gateway
        self.internet_gateway = self.attach_internet_gateway()

        # create subnet
        self.create_subnets()

        # create route tables
        self.create_route_tables()

        # create route-table routes
        self.create_routes()

        # create assosiation between subnet and route-tables
        self.create_subnet_route_table_associations()

        # create security groups
        self.create_security_groups()


        # create ecs cluster
        self.ecs_cluster = aws_ecs.Cluster(
            self, 
            'javascript-cluster', 
            vpc=self.bifrost_vpc,
            enable_fargate_capacity_providers=True,
            container_insights=True
        )


        ### outputs
        CfnOutput(self, id="ecs_vpc_id", value=self.bifrost_vpc.vpc_id)

        for k, v in self.security_group_id_to_group_map.items():
            CfnOutput(self, id=f"sg={k}", value=v.attr_group_id)

        CfnOutput(self, id="ecs_cluster_name", value=self.ecs_cluster.cluster_name)
    
    
    def attach_internet_gateway(self) -> CfnInternetGateway:
        """ Create and attach internet gateway to the VPC """
        internet_gateway = CfnInternetGateway(
            self, 
            id=config.INTERNET_GATEWAY
        )
        CfnVPCGatewayAttachment(
            self, 
            id='internet-gateway-attachment', 
            vpc_id=self.bifrost_vpc.vpc_id,
            internet_gateway_id=internet_gateway.ref
        )

        return internet_gateway
    

    def create_subnets(self):
        """ Create subnets of the VPC """
        for subnet_id, subnet_config in config.SUBNET_CONFIGURATION.items():
            subnet = CfnSubnet(
                self, 
                id=subnet_id, 
                vpc_id=self.bifrost_vpc.vpc_id, 
                cidr_block=subnet_config['cidr_block'],
                availability_zone=subnet_config['availability_zone'], 
                tags=[CfnTag(key='Name', value=subnet_id)],
                map_public_ip_on_launch=subnet_config['map_public_ip_on_launch'],
            )

            self.subnet_id_to_subnet_map[subnet_id] = subnet


    def create_route_tables(self):
        """ Create Route Tables """
        for route_table_id in config.ROUTE_TABLES_ID_TO_ROUTES_MAP:
            self.route_table_id_to_route_table_map[route_table_id] = CfnRouteTable(
                self, 
                id=route_table_id, 
                vpc_id=self.bifrost_vpc.vpc_id, 
                tags=[CfnTag(key='Name', value=route_table_id)]
            )

    def create_routes(self):
        """ Create routes of the Route Tables """
        for route_table_id, routes in config.ROUTE_TABLES_ID_TO_ROUTES_MAP.items():
            for i in range(len(routes)):
                route = routes[i]

                kwargs = {
                    **route,
                    'route_table_id': self.route_table_id_to_route_table_map[route_table_id].ref,
                }

                if route['router_type'] == RouterType.GATEWAY:
                    kwargs['gateway_id'] = self.internet_gateway.ref

                del kwargs['router_type']

                CfnRoute(self, f'{route_table_id}-route-{i}', **kwargs)


    def create_subnet_route_table_associations(self):
        """ Associate subnets with route tables """
        for subnet_id, subnet_config in config.SUBNET_CONFIGURATION.items():
            route_table_id = subnet_config['route_table_id']

            CfnSubnetRouteTableAssociation(
                self, 
                f'{subnet_id}-{route_table_id}', 
                subnet_id=self.subnet_id_to_subnet_map[subnet_id].ref,
                route_table_id=self.route_table_id_to_route_table_map[route_table_id].ref
            )


    def create_security_groups(self):
        """ Creates all the security groups """
        for security_group_id, sg_config in config.SECURITY_GROUP_ID_TO_CONFIG.items():
            self.security_group_id_to_group_map[security_group_id] = CfnSecurityGroup(
                self, 
                security_group_id, 
                vpc_id=self.bifrost_vpc.vpc_id, 
                **sg_config
            )
