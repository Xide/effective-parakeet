from pkg_resources import resource_filename
import re
import json
import boto3
import time
import datetime

# Types extracted from the EC2 pricing data from AWS.
# This report is too large to dowload and parse every time (700Mo ATOW),
# Manual extract 2019/05/20
INSTANCE_TYPES = [
    "a1.2xlarge",
    "a1.4xlarge",
    "a1.large",
    "a1.medium",
    "a1.xlarge",
    "c1.medium",
    "c1.xlarge",
    "c3.2xlarge",
    "c3.4xlarge",
    "c3.8xlarge",
    "c3.large",
    "c3.xlarge",
    "c4.2xlarge",
    "c4.4xlarge",
    "c4.8xlarge",
    "c4.large",
    "c4.xlarge",
    "c5.18xlarge",
    "c5.2xlarge",
    "c5.4xlarge",
    "c5.9xlarge",
    "c5d.18xlarge",
    "c5d.2xlarge",
    "c5d.4xlarge",
    "c5d.9xlarge",
    "c5d.large",
    "c5d.xlarge",
    "c5.large",
    "c5n.18xlarge",
    "c5n.2xlarge",
    "c5n.4xlarge",
    "c5n.9xlarge",
    "c5n.large",
    "c5n.xlarge",
    "c5.xlarge",
    "cc2.8xlarge",
    "cr1.8xlarge",
    "d2.2xlarge",
    "d2.4xlarge",
    "d2.8xlarge",
    "d2.xlarge",
    "f1.16xlarge",
    "f1.2xlarge",
    "f1.4xlarge",
    "g2.2xlarge",
    "g2.8xlarge",
    "g3.16xlarge",
    "g3.4xlarge",
    "g3.8xlarge",
    "g3s.xlarge",
    "h1.16xlarge",
    "h1.2xlarge",
    "h1.4xlarge",
    "h1.8xlarge",
    "hs1.8xlarge",
    "i2.2xlarge",
    "i2.4xlarge",
    "i2.8xlarge",
    "i2.xlarge",
    "i3.16xlarge",
    "i3.2xlarge",
    "i3.4xlarge",
    "i3.8xlarge",
    "i3en.12xlarge",
    "i3en.24xlarge",
    "i3en.2xlarge",
    "i3en.3xlarge",
    "i3en.6xlarge",
    "i3en.large",
    "i3en.xlarge",
    "i3.large",
    "i3.metal",
    "i3.xlarge",
    "m1.large",
    "m1.medium",
    "m1.small",
    "m1.xlarge",
    "m2.2xlarge",
    "m2.4xlarge",
    "m2.xlarge",
    "m3.2xlarge",
    "m3.large",
    "m3.medium",
    "m3.xlarge",
    "m4.10xlarge",
    "m4.16xlarge",
    "m4.2xlarge",
    "m4.4xlarge",
    "m4.large",
    "m4.xlarge",
    "m5.12xlarge",
    "m5.24xlarge",
    "m5.2xlarge",
    "m5.4xlarge",
    "m5a.12xlarge",
    "m5a.24xlarge",
    "m5a.2xlarge",
    "m5a.4xlarge",
    "m5ad.12xlarge",
    "m5ad.24xlarge",
    "m5ad.2xlarge",
    "m5ad.4xlarge",
    "m5ad.large",
    "m5ad.xlarge",
    "m5a.large",
    "m5a.xlarge",
    "m5d.12xlarge",
    "m5d.24xlarge",
    "m5d.2xlarge",
    "m5d.4xlarge",
    "m5d.large",
    "m5d.metal",
    "m5d.xlarge",
    "m5.large",
    "m5.metal",
    "m5.xlarge",
    "p2.16xlarge",
    "p2.8xlarge",
    "p2.xlarge",
    "p3.16xlarge",
    "p3.2xlarge",
    "p3.8xlarge",
    "p3dn.24xlarge",
    "r3.2xlarge",
    "r3.4xlarge",
    "r3.8xlarge",
    "r3.large",
    "r3.xlarge",
    "r4.16xlarge",
    "r4.2xlarge",
    "r4.4xlarge",
    "r4.8xlarge",
    "r4.large",
    "r4.xlarge",
    "r5.12xlarge",
    "r5.24xlarge",
    "r5.2xlarge",
    "r5.4xlarge",
    "r5a.12xlarge",
    "r5a.24xlarge",
    "r5a.2xlarge",
    "r5a.4xlarge",
    "r5ad.12xlarge",
    "r5ad.24xlarge",
    "r5ad.2xlarge",
    "r5ad.4xlarge",
    "r5ad.large",
    "r5ad.xlarge",
    "r5a.large",
    "r5a.xlarge",
    "r5d.12xlarge",
    "r5d.24xlarge",
    "r5d.2xlarge",
    "r5d.4xlarge",
    "r5d.large",
    "r5d.metal",
    "r5d.xlarge",
    "r5.large",
    "r5.metal",
    "r5.xlarge",
    "t1.micro",
    "t2.2xlarge",
    "t2.large",
    "t2.medium",
    "t2.micro",
    "t2.nano",
    "t2.small",
    "t2.xlarge",
    "t3.2xlarge",
    "t3a.2xlarge",
    "t3a.large",
    "t3a.medium",
    "t3a.micro",
    "t3a.nano",
    "t3a.small",
    "t3a.xlarge",
    "t3.large",
    "t3.medium",
    "t3.micro",
    "t3.nano",
    "t3.small",
    "t3.xlarge",
    "x1.16xlarge",
    "x1.32xlarge",
    "x1e.16xlarge",
    "x1e.2xlarge",
    "x1e.32xlarge",
    "x1e.4xlarge",
    "x1e.8xlarge",
    "x1e.xlarge",
    "z1d.12xlarge",
    "z1d.2xlarge",
    "z1d.3xlarge",
    "z1d.6xlarge",
    "z1d.large",
    "z1d.metal",
    "z1d.xlarge",
]


def parse_mem_to_mb(human_friendly):
    '''
    AWS expose instance ram in the "XXX GiB" format, this function
    turns it into an integer containing the number of mb.
    '''
    match = re.match('^(\d*(?:\.|,)\d+|\d+) GiB$', human_friendly)
    try:
        res = match.group(1).replace(',', '.')
        return int(float(res) * 1024)
    except Exception as e:
        print('[x] [MEM_PARSE_ERR] {}'.format(human_friendly))
        raise e


def get_instance_specs(client, instance):
    '''
    Return a dict(cls, vcpu, memory) for the instance type selected.

    Use the AWS API to fetch the specs infos for this instance,
    which are contained in the pricing infos.

    BUG: Some instances don't have pricing informations available, the
         function will return None.
    TODO: Alternative method to fetch instance specs.
    '''
    # Search product filter
    FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},'\
        '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},'\
        '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},'\
        '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},'\
        '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}}]'

    f = FLT.format(r=get_region_name(REGION), t=instance, o='Linux')
    data = client.get_products(
        ServiceCode='AmazonEC2', Filters=json.loads(f))
    try:

        attrs = json.loads(data['PriceList'][0])['product']['attributes']
        return dict(
            cls=attrs['instanceType'],
            vcpu=int(attrs['vcpu'], base=10),
            memory=parse_mem_to_mb(attrs['memory'])
        )
    except Exception as e:
        # There is no pricing information for this instance,
        print('[x] [INST_ATTR_GET] {}'.format(instance))
        return None


def get_region_name(region_code):
    '''Translate region code to region name'''

    endpoint_file = resource_filename('botocore', 'data/endpoints.json')
    with open(endpoint_file, 'r') as f:
        data = json.load(f)
    return data['partitions'][0]['regions'][region_code]['description']


def sizings(instance_type):
    '''
    Return the AWS instance sizes for the selected EC2 type (e.g: t3, m4, c5)
    Example: `sizings('c3') == ['large', '4xlarge', '8xlarge', 'xlarge', '2xlarge']`
    '''
    return list(set(map(
        lambda x: x.split('.')[1],
        filter(
            lambda y: y.startswith(instance_type),
            INSTANCE_TYPES
        )
    )))


def default_efficiency_fn(instance):
    '''
    Efficiency functions takes an instance with specs,pricing fields.
    return: Any, results will later be fed to the fitness function for evaluation.
    TODO: Weighted efficiency based on workload
    '''
    cost_efficiency = {
        'cpu': instance['pricing'] / (instance['specs']['vcpu'] * 1000),
        'mem': instance['pricing'] / instance['specs']['memory']
    }
    return cost_efficiency


def default_fitness_fn(bins, instance):
    '''
    Rank individual instances. Return a scalar.

    Here the scalar is the invert of the sum of tournament rank.
    '''
    bins[instance]['fitness'] = -(bins[instance]['rank']['cpu'] +
                                  bins[instance]['rank']['mem'])
    return bins[instance]['fitness']


class AWSSpotPricing:
    def __init__(self, region):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.ec2_client = boto3.client('ec2', region_name=region)

    def current_product_value(self, az, itp, efficiency=default_efficiency_fn):
        '''
        @param az: AWS availability zone
        @param itp: instance name in the format `type.sizing` (e.g: `t3.medium`)
        @param fitness: fn(instance) => dict(efficiency)
            `instance` will contain 'specs' and 'pricing' fields for efficiency calculation.

        @return dict(specs, pricing, efficiency)
        '''
        res = {}
        specs = get_instance_specs(self.pricing_client, itp)
        if specs is None:
            return None
        prices = self.ec2_client.describe_spot_price_history(
            InstanceTypes=[itp],
            ProductDescriptions=['Linux/UNIX (Amazon VPC)'],
            AvailabilityZone=az
        )

        res['specs'] = specs
        try:
            # Average over a week of spot prices
            latest_price = prices['SpotPriceHistory'][0]
            aggregate_end = latest_price['Timestamp'] - \
                datetime.timedelta(days=7)
            aggregate = list(filter(
                lambda x: x['Timestamp'] > aggregate_end,
                prices['SpotPriceHistory']
            ))
            res['pricing'] = sum([float(x['SpotPrice'])
                                  for x in aggregate]) / len(aggregate)
        except IndexError:
            print('[x] [NO_SPOTS] {}'.format(itp))
            return None
        res['efficiency'] = efficiency(res)
        return res

    def _bins_rank(self, bins, dims=['cpu', 'mem']):
        '''
        Add ranking informations to the bins items.

        Give rank in accordance to a scalar of the 'efficiency' dict (no nested),
        ranks are given in an ascending order (0 being the lowest efficiency)

        Handles ex-aequo (some ranks may be shared by multiple elements)
        '''

        e_dims = {}
        for d in dims:
            e_dims[d] = sorted(
                bins.keys(),
                key=lambda x: bins[x]['efficiency'][d]
            )

        def podium_rank(x, l):
            '''uniq the list up to the current element index, our element is at rank len(list)'''
            return len(list(set(l[:x+1])))

        for itp in bins.keys():
            bins[itp]['rank'] = {
                x: podium_rank(e_dims[x].index(itp), e_dims[x]) for x in dims
            }

        return bins

    def relative_worth_analysis(self, types, fitness=default_fitness_fn, azs=['a']):
        '''
        Iterate over all the sizings of the `types` to find the best efficiency
        @return list of instances sorted by efficiency : {specs, pricing, efficiency}

        Instance efficiency sorting can be controlled with the `fitness` parameter.
        '''
        bins = {}
        # TODO: Multiple AZ's
        # WARN: bins keys will collide on multiple az
        # for az in ['{}{}'.format(self.region, x) for x in azs]:
        az = '{}{}'.format(self.region, azs[0])
        for instance_type in types:
            available_sizings = sizings(instance_type)
            print(
                '[-] {} : {}'.format(
                    instance_type,
                    available_sizings
                )
            )

            for sizing in available_sizings:
                itp = '{}.{}'.format(instance_type, sizing)
                x = self.current_product_value(az, itp)
                if x is None:
                    continue
                bins[itp] = x

        bins = self._bins_rank(bins)

        # First indices will be the contenders with the better fitness
        podium = sorted(
            bins.keys(),
            key=lambda x: -(fitness(bins, x))
        )
        for sizing in podium:
            print('- {}: {}'.format(sizing, bins[sizing]))

        return podium


if __name__ == '__main__':
    REGION = 'eu-west-1'
    # Test with all the instance types
    # AVAILABLE_TYPES = set(map(lambda x: x.split('.')[0], INSTANCE_TYPES))
    # AWSSpotPricing(REGION).relative_worth_analysis(AVAILABLE_TYPES)
    AWSSpotPricing(REGION).relative_worth_analysis(['t3'])
