"""Command-line interface for cluster management"""
import click
import requests
import json
from typing import Optional


@click.group()
@click.option('--host', default='localhost', help='Cluster host')
@click.option('--port', default=8001, help='Cluster port')
@click.pass_context
def cli(ctx, host, port):
    """Cluster management CLI"""
    ctx.ensure_object(dict)
    ctx.obj['base_url'] = f"http://{host}:{port}/api/v1"


@cli.command()
@click.pass_context
def status(ctx):
    """Show cluster status"""
    try:
        response = requests.get(f"{ctx.obj['base_url']}/cluster/status")
        response.raise_for_status()
        
        data = response.json()
        click.echo(f"Cluster Status: {data['cluster_status']}")
        click.echo(f"Total Nodes: {data['total_nodes']}")
        click.echo(f"Healthy Nodes: {data['healthy_nodes']}")
        click.echo(f"Leader ID: {data['leader_id']}")
        
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.pass_context
def nodes(ctx):
    """List all nodes"""
    try:
        response = requests.get(f"{ctx.obj['base_url']}/nodes")
        response.raise_for_status()
        
        nodes = response.json()
        click.echo("Node Status:")
        click.echo("-" * 50)
        
        for node in nodes:
            status_icon = "🟢" if node['status'] == 'healthy' else "🔴"
            leader_mark = " (LEADER)" if node.get('leader_id') == node['node_id'] else ""
            click.echo(f"{status_icon} Node {node['node_id']}: {node['status']}{leader_mark}")
            
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('node_id', type=int)
@click.pass_context
def node(ctx, node_id):
    """Show specific node details"""
    try:
        response = requests.get(f"{ctx.obj['base_url']}/nodes/{node_id}")
        response.raise_for_status()
        
        node = response.json()
        click.echo(f"Node {node_id} Details:")
        click.echo(f"  Status: {node['status']}")
        click.echo(f"  Leader ID: {node['leader_id']}")
        click.echo(f"  Uptime: {node['uptime']:.1f}s")
        click.echo(f"  Last Heartbeat: {node['last_heartbeat']:.1f}s ago")
        
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('node_id', type=int)
@click.pass_context
def metrics(ctx, node_id):
    """Show node metrics"""
    try:
        response = requests.get(f"{ctx.obj['base_url']}/nodes/{node_id}/metrics")
        response.raise_for_status()
        
        metrics = response.json()
        click.echo(f"Node {node_id} Metrics:")
        click.echo(f"  CPU Usage: {metrics['cpu_percent']:.1f}%")
        click.echo(f"  Memory Usage: {metrics['memory_percent']:.1f}%")
        click.echo(f"  Active Connections: {metrics['active_connections']}")
        
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option('--token', required=True, help='Admin authentication token')
@click.pass_context
def election(ctx, token):
    """Trigger leader election"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(f"{ctx.obj['base_url']}/cluster/election", headers=headers)
        response.raise_for_status()
        
        click.echo("Leader election triggered successfully")
        
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('node_id', type=int)
@click.option('--token', required=True, help='Admin authentication token')
@click.pass_context
def restart(ctx, node_id, token):
    """Restart a node"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(f"{ctx.obj['base_url']}/nodes/{node_id}/restart", headers=headers)
        response.raise_for_status()
        
        click.echo(f"Node {node_id} restart initiated")
        
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == '__main__':
    cli()