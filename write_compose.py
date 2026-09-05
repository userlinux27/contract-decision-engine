import yaml

# Custom representer to keep lists in flow style
def represent_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.add_representer(list, represent_list)

data = {
    'version': '3.8',
    'services': {
        'app': {
            'build': {'context': '.', 'dockerfile': 'Dockerfile'},
            'container_name': 'contract-decision-engine-app',
            'expose': ['8000'],
            'volumes': ['./uploads:/app/uploads', './data:/app/data', './fixtures:/app/fixtures'],
            'environment': ['PYTHONUNBUFFERED=1', 'LLM_PROVIDER=stub'],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'python', '-c', 'import urllib.request; urllib.request.urlopen("http://localhost:8000/api/health")'],
                'interval': '30s',
                'timeout': '3s',
                'start_period': '10s',
                'retries': 3
            },
            'networks': ['cde-network']
        },
        'nginx': {
            'image': 'nginx:alpine',
            'container_name': 'contract-decision-engine-nginx',
            'ports': ['80:80', '443:443'],
            'volumes': ['./nginx.conf:/etc/nginx/nginx.conf:ro', './certs:/etc/nginx/certs:ro'],
            'depends_on': {'app': {'condition': 'service_healthy'}},
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'wget', '-q', '--spider', 'http://localhost/health'],
                'interval': '30s',
                'timeout': '3s',
                'start_period': '5s',
                'retries': 3
            },
            'networks': ['cde-network']
        }
    },
    'networks': {
        'cde-network': {'name': 'cde-network', 'driver': 'bridge'}
    }
}

with open('docker-compose.yml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
print('docker-compose.yml written')
