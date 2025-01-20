import os
import sys
import threading
import time
from datetime import datetime
from threading import Lock
from flask import request
import requests
from app.config import Config
from service.udp_service import UdpService
from service.tcp_service import (
    send_tcp_request,
    send_tcp_request_and_get_response_body,
)
from utils.logger import global_logger
from utils.uuid_generator import UuidGenerator

from model.star import Star


class SolService:
    def __init__(self, peer, star_port=None):
        self.peer = peer
        self.star_uuid = None
        self.sol_uuid = None
        self.star_port = star_port or Config.STAR_PORT
        self.num_active_components = 1
        self.sol = None
        self.star_list = []
        self.galaxy_lock = Lock()

    def listen_for_hello(self, port):
        """Listens for HELLO? messages and responds with the required JSON blob."""
        global_logger.info("SOL is listening for HELLO? messages...")

        try:

            def handle_message(message, addr):
                parts = message.strip().split()
                if message.strip() == "HELLO?":
                    global_logger.info(f"Received HELLO? from {addr[0]}:{addr[1]}")
                    self.send_response(addr[0], Config.STAR_PORT)

                elif (
                    len(parts) == 4
                    and parts[0] == "HELLO?"
                    and parts[1] == "I"
                    and parts[2] == "AM"
                ):
                    star_uuid = parts[3]
                    global_logger.info(f"Received HELLO? from {addr[0]}:{addr[1]}")
                    # ist star uid bekannt?
                    with self.galaxy_lock:
                        saved_star = self.get_star(star_uuid)
                    if saved_star is None:
                        # post schicken
                        global_logger.info(f"Sending star-POST to {addr[0]}")
                        res_body = self.send_galaxy_post(addr[0])
                        if res_body is None:
                            return
                        star = res_body.get("star")
                        sol = res_body.get("sol")
                        sol_ip = res_body.get("sol-ip")
                        sol_tcp = res_body.get("sol-tcp")
                        no_com = res_body.get("no-com")
                        status = res_body.get("status")
                        self.add_star(star, sol, sol_ip, sol_tcp, no_com, status)
                    else:
                        if (
                            saved_star.sol_ip == addr[0]
                        ):  # star schon bekannt und ip stimmt
                            # patch schicken
                            self.send_galaxy_patch(addr[0])
                else:
                    global_logger.warning(
                        f"Unexpected message from {addr[0]}:{addr[1]}: {message}"
                    )

            UdpService.listen(port, callback=handle_message)

        except Exception as e:
            global_logger.error(f"Error while listening for HELLO? messages: {e}")

    def send_galaxy_post(self, addr):
        saved_star_url = f"http://{addr}:{Config.GALAXY_PORT}/vs/v1/star"

        response = {
            "star": self.star_uuid,
            "sol": self.sol_uuid,
            "sol-ip": Config.IP,
            "sol-tcp": self.star_port,
            "no-com": self.sol.num_active_components,
            "status": 200,
        }
        headers = {"Content-Type": "application/json"}
        return send_tcp_request_and_get_response_body(
            "POST", saved_star_url, body=response, headers=headers
        )

    def send_galaxy_patch(self, addr):
        saved_star_url = f"http://{addr}:{Config.GALAXY_PORT}/vs/v1/star/{self.star_uuid}"

        response = {
            "star": self.star_uuid,
            "sol": self.sol_uuid,
            "sol-ip": Config.IP,
            "sol-tcp": self.star_port,
            "no-com": self.sol.num_active_components,
            "status": 200,
        }
        headers = {"Content-Type": "application/json"}
        return send_tcp_request("PATCH", saved_star_url, body=response, headers=headers)

    def send_response(self, target_ip, target_port):
        """Send the JSON blob response to the sender of the HELLO? message."""
        response = {
            "star": self.star_uuid,
            "sol": self.sol_uuid,
            "sol-ip": Config.IP,
            "sol-tcp": self.star_port,
            "component": UuidGenerator.generate_com_uuid(),
        }
        global_logger.info(f"Sending response to {target_ip}:{target_port}: {response}")
        try:
            UdpService.send_response(response, target_ip, target_port)
        except Exception as e:
            global_logger.error(
                f"Failed to send response to {target_ip}:{target_port}: {e}"
            )

    def check_component_status(self, peer):
        """
        Überprüft den Status einer Komponente über eine GET-Anfrage.
        """
        url = f"http://{peer.com_ip}:{peer.com_tcp}/vs/v1/system/{peer.com_uuid}?star={self.star_uuid}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                global_logger.info(f"Component {peer.com_uuid} is active.")
                peer.set_last_interaction_timestamp()
            else:
                global_logger.warning(
                    f"Component {peer.com_uuid} returned status {response.status_code}."
                )
        except requests.RequestException as e:
            global_logger.error(f"Failed to contact component {peer.com_uuid}: {e}")
            peer.status = "disconnected"

    def check_peer_health(self):
        """Checks the health of registered peers and updates their status."""
        while True:
            try:
                current_time = datetime.now()
                with self.sol.peers_lock:
                    for peer in self.sol.registered_peers:

                        if peer.com_uuid == self.peer.com_uuid:
                            continue

                        last_interaction = datetime.fromisoformat(
                            peer.last_interaction_timestamp
                        )
                        if (
                            current_time - last_interaction
                        ).total_seconds() > Config.PEER_INACTIVITY_THRESHOLD:
                            global_logger.warning(
                                f"Component {peer.com_uuid} is inactive. Checking status."
                            )
                            self.check_component_status(peer)
                time_after_check = datetime.now()
                time_elapsed = int((time_after_check - current_time).total_seconds())
                time.sleep(Config.PEER_INACTIVITY_THRESHOLD - time_elapsed)
            except Exception as e:
                global_logger.error(f"Error in check_peer_health thread: {e}")

    def unregister_all_peers_and_exit(self):
        """Unregister all peers from the star and exit SOL."""
        global_logger.info("Unregistering all peers before exiting...")
        with self.sol.peers_lock:
            for peer in self.sol.registered_peers:
                self._unregister_peer(peer)
            self.sol.registered_peers.clear()

        # see all running threads
        # Print all active threads before exiting
        # global_logger.info("Active threads before exit:")
        # active_threads = threading.enumerate()
        # for thread in active_threads:
        #     global_logger.info(f"Thread ID: {thread.ident}, Name: {thread.name}, Daemon: {thread.daemon}")
        global_logger.info("All peers processed. Exiting SOL...")
        os._exit(Config.EXIT_CODE_SUCCESS)

    def _unregister_peer(self, peer):
        """Helper method to unregister a single peer."""
        url = f"http://{peer.ip}:{peer.com_tcp}/vs/v1/system/{peer.com_uuid}?star={self.star_uuid}"
        for attempt in range(Config.UNREGISTER_RETRY_COUNT):
            try:
                global_logger.info(
                    f"Sending DELETE request to peer {peer.com_uuid} at {url}"
                )
                response = requests.delete(url)
                if response.status_code == 200:
                    global_logger.info(
                        f"Peer {peer.com_uuid} unregistered successfully."
                    )
                    return
                elif response.status_code == 401:
                    global_logger.warning(
                        f"Unauthorized attempt to unregister peer {peer.com_uuid}. Skipping."
                    )
                    return
                else:
                    global_logger.warning(
                        f"Unexpected response from peer {peer.com_uuid}: {response.status_code}"
                    )
            except requests.RequestException as e:
                global_logger.error(f"Failed to contact peer {peer.com_uuid}: {e}")

            global_logger.warning(
                f"Retrying DELETE request to peer {peer.com_uuid}... ({attempt + 1}/{Config.UNREGISTER_RETRY_COUNT})"
            )
            time.sleep(Config.UNREGISTER_RETRY_DELAY[attempt])

        global_logger.error(
            f"Failed to unregister peer {peer.com_uuid} after {Config.UNREGISTER_RETRY_COUNT} attempts."
        )
        peer.status = "disconnected"

    def unregister_at_galaxy(self):
        global_logger.info("Unregistering from Galaxy...")
        with self.galaxy_lock:
            for star in self.star_list:
                if star.status != 200:
                    continue
                self._unregister_star(star)
        global_logger.info("Succesfully unregistered from Galaxy...")

    def _unregister_star(self, star):
        """
        Helper method to unregister a star.
        """
        url = f"http://{star.sol_ip}:{Config.GALAXY_PORT}{Config.API_BASE_URL_STAR}{self.star_uuid}"
        for attempt in range(Config.UNREGISTER_RETRY_COUNT):
            try:
                global_logger.info(
                    f"Sending DELETE request to unregister star {self.star_uuid} at {url}"
                )
                response = requests.delete(url)
                if response.status_code == 200:
                    global_logger.info(
                        f"Star {self.star_uuid} unregistered successfully at Star {star.star_uuid}."
                    )
                    return
                elif response.status_code == 401 or response.status_code == 404:
                    global_logger.warning(
                        f"Unauthorized attempt to unregister at star {star.star_uuid}. Skipping."
                    )
                    return
                else:
                    global_logger.warning(
                        f"Unexpected response from star {star.star_uuid}: {response.status_code}"
                    )
            except requests.RequestException as e:
                global_logger.error(f"Failed to contact star {star.star_uuid}: {e}")

            global_logger.warning(
                f"Retrying DELETE request at star {star.star_uuid}... ({attempt + 1}/{Config.UNREGISTER_RETRY_COUNT})"
            )
            time.sleep(Config.UNREGISTER_RETRY_DELAY[attempt])

        global_logger.error(
            f"Failed to unregister at star {star.star_uuid} after {Config.UNREGISTER_RETRY_COUNT} attempts."
        )

    def add_star(self, star_uuid, sol_uuid, sol_ip, sol_tcp, no_com, status):
        """
        Fügt einen neuen Stern zur Starlist hinzu, wenn er noch nicht existiert.
        """
        with self.galaxy_lock:
            if not any(
                existing_star.star_uuid == star_uuid for existing_star in self.star_list
            ):
                new_star = Star(star_uuid, sol_uuid, sol_ip, sol_tcp, no_com, status)
                self.star_list.append(new_star)
                list_str = ""
                for star in self.star_list:
                    list_str += str(star.to_dict()) + "\n"
                global_logger.info(f"Galaxy updated: \n{list_str}")
            else:
                old_entry = self.get_star(star_uuid)
                old_entry.status = status

    def get_star_list(self):
        """
        Gibt die Liste aller bekannten Sterne zurück.
        """
        return self.star_list

    def get_star(self, star_uuid):

        return next(
            (star for star in self.star_list if star.star_uuid == star_uuid), None
        )
