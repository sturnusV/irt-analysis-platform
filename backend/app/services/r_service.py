import requests
import os
import logging
import json
import time
import random

logger = logging.getLogger(__name__)

class RServiceClient:
    def __init__(self):
        self.base_url = os.getenv("R_SERVICE_URL", "http://r-service:8001")
        self.timeout = 300
        self.use_fallback = False
    
    def health_check(self):
        """Check if R service is healthy"""
        if self.use_fallback:
            return False
            
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"R service health check failed with status {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"R service health check failed: {e}")
            self.use_fallback = True
            return False
    
    def analyze_irt(self, file_path: str) -> dict:
        url = f"{self.base_url}/analyze"
        
        # Send as JSON, not form data
        payload = {"data_path": file_path}
        
        try:
            response = requests.post(
                url, 
                json=payload,
                timeout=120
            )
            
            # Check for non-200 status
            if response.status_code != 200:
                error_msg = response.text if response.text else "R service returned non-200 status."
                logger.error(f"R service returned status {response.status_code}. Raw response: {error_msg}")
                raise Exception(f"R service status error: {error_msg}")

            # Try to parse the JSON response
            try:
                result = response.json()
            except json.JSONDecodeError:
                logger.error(f"R service returned non-JSON response. Raw text: {response.text}")
                raise Exception(f"R service returned invalid response: {response.text[:100]}...")

            # Check for the Plumber internal error format
            if result.get("status") == "error":
                error_msg = result.get("error", "Unknown error message from R service.")
                logger.error(f"R service reported FAILURE (status: error). Error: {error_msg}")
                raise Exception(f"IRT analysis failed in R service: {error_msg}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling R service: {e}")
            raise Exception(f"Network error calling R service: {e}")

    def get_icc(self, data_path: str, item_id: str = None):
        """Get ICC curves from R service."""
        try:
            payload = {"data_path": data_path}
            if item_id:
                payload["item_id"] = item_id

            response = requests.post(
                f"{self.base_url}/icc",
                json=payload,
                timeout=90
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "error": f"ICC endpoint returned {response.status_code}"
                }

            data = response.json()
            if data.get("status") != "success":
                return {
                    "status": "error",
                    "error": data.get("error", "ICC failed")
                }

            return data

        except Exception as e:
            logger.error(f"ICC generation failed: {e}")
            return {"status": "error", "error": str(e)}

    # -----------------------------------------------------------------
    # NEW METHOD: Get Item Information Function (IIF)
    # -----------------------------------------------------------------
    def get_iif(self, data_path: str):
        """
        Call R service to get Item Information Function (IIF) data.
        """
        url = f"{self.base_url}/iif"
        try:
            logger.info(f"=== R IIF CALL STARTED ===")
            logger.info(f"URL: {url}")
            logger.info(f"Data path: {data_path}")
            
            response = requests.post(
                url,
                json={"data_path": data_path},
                timeout=120
            )
            
            logger.info(f"R IIF response status: {response.status_code}")
            logger.info(f"R IIF response content length: {len(response.content)}")
            
            # Check if response is valid JSON
            try:
                data = response.json()
                logger.info(f"R IIF parsed JSON successfully. Keys: {list(data.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"R IIF JSON decode error: {e}")
                logger.error(f"Response text: {response.text[:500]}...")
                raise Exception(f"R service returned invalid JSON: {e}")
            
            # Check for success status
            if data.get("status") != "success":
                error_msg = data.get('error', 'Unknown error from R service')
                logger.error(f"R IIF service returned error: {error_msg}")
                raise Exception(f"IIF calculation failed: {error_msg}")
            
            # Log success details
            if 'iif_data' in data:
                logger.info(f"R IIF SUCCESS: {len(data['iif_data'])} rows received")
                if data['iif_data']:
                    sample = data['iif_data'][:2]  # First 2 rows
                    logger.info(f"IIF data sample: {sample}")
            else:
                logger.warning("R IIF response missing 'iif_data' key")
                
            logger.info("=== R IIF CALL COMPLETED SUCCESSFULLY ===")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"R IIF RequestException: {e}")
            raise Exception(f"R service request failed: {e}")
        except Exception as e:
            logger.error(f"R IIF Unexpected error: {e}")
            raise


    def get_test_info(self, data_path: str):
        """
        Call R service to get test information function
        """
        try:
            response = requests.post(
                f"{self.base_url}/testinfo",
                json={"data_path": data_path},
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"R TIF service call failed: {e}")
            raise


# Global R service client instance
r_service = RServiceClient()