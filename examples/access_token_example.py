#!/usr/bin/env python3
"""
BGG Access Token Example

This example demonstrates how to use the BoardGameGeek library with
access tokens for API authentication.

To use this example:
1. Register at BoardGameGeek and obtain your access token
2. Replace 'your_bgg_access_token' with your actual token
3. Run the script

For more information on BGG access tokens, see:
https://boardgamegeek.com/thread/3525319/registration-to-use-the-xml-api-and-obtain-soon-to
"""

from boardgamegeek import BGGClient, BGGClientLegacy, CacheBackendNone

def example_with_access_token():
    """Example using BGGClient with access token."""
    print("Example: BGGClient with Access Token")
    print("-" * 40)
    
    # Replace with your actual BGG access token
    access_token = "your_bgg_access_token"
    
    # Create client with access token
    bgg = BGGClient(access_token=access_token)
    
    print(f"Client created with token: {access_token[:10]}...")
    
    # Example: Get game information
    # Note: This would make an actual API call if run with a real token
    print("\nTo use this client, you would call:")
    print("game = bgg.game('Monopoly')")
    print("print(f'Game: {game.name}, Year: {game.year}')")
    
    print("\nAll API calls will include the Authorization header:")
    headers = bgg._get_auth_headers()
    print(f"Headers: {headers}")

def example_without_access_token():
    """Example using BGGClient without access token (backward compatibility)."""
    print("\n\nExample: BGGClient without Access Token (Backward Compatible)")
    print("-" * 60)
    
    # Create client without access token (existing behavior)
    bgg = BGGClient()
    
    print("Client created without token (backward compatible)")
    print("Token:", bgg._access_token)
    print("Headers:", bgg._get_auth_headers())

def example_legacy_api():
    """Example using BGGClientLegacy with access token."""
    print("\n\nExample: BGGClientLegacy with Access Token")
    print("-" * 45)
    
    # Replace with your actual BGG access token
    access_token = "your_bgg_access_token"
    
    # Create legacy client with access token
    bgg_legacy = BGGClientLegacy(access_token=access_token)
    
    print(f"Legacy client created with token: {access_token[:10]}...")
    print("Headers:", bgg_legacy._get_auth_headers())

def example_with_other_parameters():
    """Example combining access token with other parameters."""
    print("\n\nExample: BGGClient with Access Token and Other Parameters")
    print("-" * 60)
    
    # Combine access token with other configuration options
    bgg = BGGClient(
        access_token="your_bgg_access_token",
        cache=CacheBackendNone(),  # Disable caching
        timeout=30,                # 30 second timeout
        retries=5,                 # 5 retries on failure
        retry_delay=3              # 3 second delay between retries
    )
    
    print("Client created with:")
    print(f"  - Access token: {bgg._access_token[:10] if bgg._access_token else None}...")
    print(f"  - Timeout: {bgg._timeout} seconds")
    print(f"  - Retries: {bgg._retries}")
    print(f"  - Retry delay: {bgg._retry_delay} seconds")

def main():
    """Run all examples."""
    print("BGG Access Token Examples")
    print("=" * 50)
    
    example_with_access_token()
    example_without_access_token()
    example_legacy_api()
    example_with_other_parameters()
    
    print("\n\nNext Steps:")
    print("1. Register at BoardGameGeek to get your access token")
    print("2. Replace 'your_bgg_access_token' with your actual token")
    print("3. Start making authenticated API calls!")
    print("\nFor more information, visit:")
    print("https://boardgamegeek.com/thread/3525319/registration-to-use-the-xml-api-and-obtain-soon-to")

if __name__ == "__main__":
    main()