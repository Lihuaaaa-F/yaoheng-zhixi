"""原生服务启停探针必须区分活跃监听与关闭后的 TCP 状态。"""
import runpy
import socket
from pathlib import Path


def _occupied():
    return runpy.run_path(str(Path(__file__).parents[1] / 'scripts/manage.py'))['occupied']


def test_port_probe_allows_restart_after_server_closes_connection():
    occupied = _occupied()
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', 0))
        port = server.getsockname()[1]
        server.listen()
        with socket.create_connection(('127.0.0.1', port)) as client:
            accepted, _ = server.accept()
            accepted.close()  # 服务端主动关闭，留下该端口的 TIME_WAIT。
            assert client.recv(1) == b''
    assert not occupied(port)


def test_port_probe_still_rejects_a_live_listener():
    occupied = _occupied()
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', 0))
        server.listen()
        assert occupied(server.getsockname()[1])
