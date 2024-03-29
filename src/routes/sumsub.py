"""Sumsub Routes."""
from http.client import HTTPException
from fastapi import Depends
from fastapi import FastAPI
from typing import Self

from src.schemas import SuccessOrFailureResponse, SumsubApplicantStatus
from src.utils import RouterUtils
from src.sumsub import generate_sumsub_token
from src.firestore import db
from src.firestore.crud import check_locked, check_and_lock_user

from google.cloud import firestore
from google.cloud.firestore_v1.transaction import Transaction

from fastapi import HTTPException
import time
import logging

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class SumsubRouter():

    def __init__(self: Self, app: FastAPI) -> None:
        self.app = app

        @app.get("/onboard/status", response_model=SumsubApplicantStatus)
        async def onboard_status(
            user: str = Depends(RouterUtils.get_user_token)
        ) -> SumsubApplicantStatus:
            """Query Firestore to see if the user has been onboarded yet.

            Only one request can be in progress at a time for a given user.
            This is verified by checking if the user id is "locked" in firestore.

            Args:
                user (str): The user to submit the application for.

            Returns:
                str: The user status
            """
            # Check if the user is locked
            if check_locked(user):
                raise HTTPException(
                    status_code=400,
                    detail="Duplicate request is already in progress"
                )

            # Initialize a Firestore transaction
            transaction = db.transaction()

            # Check and lock the user in the transaction
            try:
                return check_and_lock_user(transaction, user)
            except Exception as e:
                LOG.exception(e)
                transaction.rollback()
                raise HTTPException(status_code=400, detail=str(e))

        # TODO: not sure if this is needed
        @app.get("/onboard/id", response_model=dict)
        async def get_applicant_id(user: str = Depends(RouterUtils.get_user_token)) -> str:
            """Fetch the applicant_id for the given user from Firestore.

            Args:
                user (str): The user to fetch the applicant_id for.

            Returns:
                str: The applicant_id for the user
            """
            user_ref = db.collection('users').document(user)
            doc = user_ref.get()

            if not doc.exists:
                LOG.debug(f"User {user} not found.")
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )

            user_data = doc.to_dict()
            applicant_id = user_data.get('applicant_id')
            LOG.debug(f"Applicant ID for user {user} is {applicant_id}")
            return applicant_id

        @app.get("/onboard/token", response_model=dict)
        async def sumsub_token(
            user: str = Depends(RouterUtils.get_user_token)
        ) -> dict:
            """Generates a Sumsub access token and returns it.

            Args:
                user (str): The user to submit the application for.

            Returns:
                dict: A dictionary containing the newly generated access token.
            """
            level_name = 'basic-kyc-level'  # replace with your level name
            try:
                token = generate_sumsub_token(user, level_name)
                LOG.debug(f"Generated Sumsub access token for user {user}")
                return {'token': token}
            except Exception as e:
                LOG.exception(e)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate Sumsub access token"
                )
