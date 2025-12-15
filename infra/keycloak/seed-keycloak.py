#!/usr/bin/env python3
"""
Seed Keycloak with Template realm and clients.
Requires: pip install requests
Usage: python seed-keycloak.py [--keycloak-url http://localhost:8080]
"""
import argparse
import json
import sys
import time

try:
    import requests
except ImportError:
    print("Error: requests module not found")
    print("Install: pip install requests")
    sys.exit(1)

# ============================================================================
# Configuration - Customize these for your project
# ============================================================================
REALM_NAME = "template"
REALM_DISPLAY = "Template Platform"
CLIENT_ID = "template-web"
CLIENT_NAME = "Template Web Application"
ROLES = ["ADMIN", "GESTOR", "OPERADOR", "VIEWER"]
DEFAULT_ADMIN_EMAIL = "admin@template.com"
DEFAULT_ADMIN_PASS = "admin123"

class KeycloakSeeder:
    def __init__(self, base_url: str, admin_user: str = "admin", admin_pass: str = "admin"):
        self.base_url = base_url.rstrip('/')
        self.admin_user = admin_user
        self.admin_pass = admin_pass
        self.token = None
        
    def wait_for_keycloak(self, timeout: int = 60):
        """Wait for Keycloak to be ready."""
        print(f"Waiting for Keycloak at {self.base_url}...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/", timeout=2)
                if resp.status_code in [200, 404]:
                    print("✓ Keycloak is ready")
                    return True
            except:
                pass
            time.sleep(2)
        print("✗ Keycloak not ready after timeout")
        return False
    
    def get_admin_token(self):
        """Get admin access token."""
        print("Getting admin token...")
        resp = requests.post(
            f"{self.base_url}/realms/master/protocol/openid-connect/token",
            data={
                "client_id": "admin-cli",
                "username": self.admin_user,
                "password": self.admin_pass,
                "grant_type": "password"
            }
        )
        resp.raise_for_status()
        self.token = resp.json()['access_token']
        print("✓ Got admin token")
        return self.token
    
    def headers(self):
        """Get authorization headers."""
        if not self.token:
            self.get_admin_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def realm_exists(self, realm_name: str) -> bool:
        """Check if realm exists."""
        resp = requests.get(
            f"{self.base_url}/admin/realms/{realm_name}",
            headers=self.headers()
        )
        return resp.status_code == 200
    
    def create_realm(self):
        """Create realm."""
        if self.realm_exists(REALM_NAME):
            print(f"✓ Realm '{REALM_NAME}' already exists")
            return
        
        print(f"Creating realm '{REALM_NAME}'...")
        realm_config = {
            "realm": REALM_NAME,
            "enabled": True,
            "displayName": REALM_DISPLAY,
            "sslRequired": "none",  # dev only - change for production
            "registrationAllowed": False,
            "loginWithEmailAllowed": True,
            "duplicateEmailsAllowed": False,
            "resetPasswordAllowed": True,
            "editUsernameAllowed": False,
            "bruteForceProtected": True,
        }
        
        resp = requests.post(
            f"{self.base_url}/admin/realms",
            headers=self.headers(),
            json=realm_config
        )
        resp.raise_for_status()
        print(f"✓ Realm '{REALM_NAME}' created")
    
    def create_client(self):
        """Create web client."""
        print(f"Creating client '{CLIENT_ID}'...")
        
        # Check if exists
        resp = requests.get(
            f"{self.base_url}/admin/realms/{REALM_NAME}/clients?clientId={CLIENT_ID}",
            headers=self.headers()
        )
        clients = resp.json()
        if clients:
            print(f"✓ Client '{CLIENT_ID}' already exists")
            return clients[0]['id']
        
        client_config = {
            "clientId": CLIENT_ID,
            "name": CLIENT_NAME,
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True,
            "implicitFlowEnabled": False,
            "serviceAccountsEnabled": False,
            "redirectUris": [
                "http://localhost:3000/*",
                "http://localhost:5173/*",
                "http://localhost:13000/*"
            ],
            "webOrigins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:13000"
            ],
            "protocol": "openid-connect",
            "attributes": {
                "pkce.code.challenge.method": "S256"
            }
        }
        
        resp = requests.post(
            f"{self.base_url}/admin/realms/{REALM_NAME}/clients",
            headers=self.headers(),
            json=client_config
        )
        resp.raise_for_status()
        print(f"✓ Client '{CLIENT_ID}' created")
        
        # Get client ID
        resp = requests.get(
            f"{self.base_url}/admin/realms/{REALM_NAME}/clients?clientId={CLIENT_ID}",
            headers=self.headers()
        )
        return resp.json()[0]['id']
    
    def create_roles(self):
        """Create realm roles."""
        print("Creating roles...")
        for role in ROLES:
            resp = requests.get(
                f"{self.base_url}/admin/realms/{REALM_NAME}/roles/{role}",
                headers=self.headers()
            )
            if resp.status_code == 200:
                print(f"  ✓ Role '{role}' already exists")
                continue
            
            resp = requests.post(
                f"{self.base_url}/admin/realms/{REALM_NAME}/roles",
                headers=self.headers(),
                json={"name": role, "description": f"{role} role"}
            )
            resp.raise_for_status()
            print(f"  ✓ Role '{role}' created")
    
    def create_admin_user(self):
        """Create default admin user."""
        print(f"Creating admin user '{DEFAULT_ADMIN_EMAIL}'...")
        
        # Check if exists
        resp = requests.get(
            f"{self.base_url}/admin/realms/{REALM_NAME}/users?email={DEFAULT_ADMIN_EMAIL}",
            headers=self.headers()
        )
        users = resp.json()
        if users:
            print(f"✓ User '{DEFAULT_ADMIN_EMAIL}' already exists")
            return users[0]['id']
        
        user_config = {
            "username": DEFAULT_ADMIN_EMAIL,
            "email": DEFAULT_ADMIN_EMAIL,
            "enabled": True,
            "emailVerified": True,
            "firstName": "Admin",
            "lastName": "User",
            "credentials": [{
                "type": "password",
                "value": DEFAULT_ADMIN_PASS,
                "temporary": False
            }]
        }
        
        resp = requests.post(
            f"{self.base_url}/admin/realms/{REALM_NAME}/users",
            headers=self.headers(),
            json=user_config
        )
        resp.raise_for_status()
        
        # Get user ID
        resp = requests.get(
            f"{self.base_url}/admin/realms/{REALM_NAME}/users?email={DEFAULT_ADMIN_EMAIL}",
            headers=self.headers()
        )
        user_id = resp.json()[0]['id']
        
        # Assign all roles
        for role in ROLES:
            role_resp = requests.get(
                f"{self.base_url}/admin/realms/{REALM_NAME}/roles/{role}",
                headers=self.headers()
            )
            role_data = role_resp.json()
            
            requests.post(
                f"{self.base_url}/admin/realms/{REALM_NAME}/users/{user_id}/role-mappings/realm",
                headers=self.headers(),
                json=[role_data]
            )
        
        print(f"✓ User '{DEFAULT_ADMIN_EMAIL}' created with all roles")
        return user_id
    
    def seed(self):
        """Run complete seeding."""
        print("\n" + "="*60)
        print(f"  KEYCLOAK SEEDER - {REALM_DISPLAY}")
        print("="*60 + "\n")
        
        if not self.wait_for_keycloak():
            sys.exit(1)
        
        self.get_admin_token()
        self.create_realm()
        self.create_client()
        self.create_roles()
        self.create_admin_user()
        
        print("\n" + "="*60)
        print("  SEEDING COMPLETE!")
        print("="*60)
        print(f"\n  Realm: {REALM_NAME}")
        print(f"  Client: {CLIENT_ID}")
        print(f"  Roles: {', '.join(ROLES)}")
        print(f"\n  Test User: {DEFAULT_ADMIN_EMAIL}")
        print(f"  Password: {DEFAULT_ADMIN_PASS}")
        print(f"\n  Keycloak Admin: {self.base_url}")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Seed Keycloak with template realm")
    parser.add_argument("--keycloak-url", default="http://localhost:8080", help="Keycloak base URL")
    parser.add_argument("--admin-user", default="admin", help="Keycloak admin username")
    parser.add_argument("--admin-pass", default="admin", help="Keycloak admin password")
    args = parser.parse_args()
    
    seeder = KeycloakSeeder(args.keycloak_url, args.admin_user, args.admin_pass)
    seeder.seed()


if __name__ == "__main__":
    main()
