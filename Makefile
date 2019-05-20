data/aws_ec2_pricing.json:
	@mkdir -p data
	curl -o data/aws_ec2_pricing.json --fail -fSSL https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json

data/instance_types.txt: data/aws_ec2_pricing.json
	jq -r '.products[].attributes.instanceType' data/aws_ec2_pricing.json | sort | uniq > data/instance_types.txt

data/locations.txt: data/aws_ec2_pricing.json
	jq -r '.products[].attributes.location' data/aws_ec2_pricing.json | sort | uniq > data/locations.txt
