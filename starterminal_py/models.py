from pydantic import BaseModel, Field


class RegisterCardRequest(BaseModel):
    card_id: str = Field(min_length=4, max_length=128)
    pin: str = Field(min_length=4, max_length=12)
    owner_name: str = Field(min_length=1, max_length=100)
    telegram_chat_id: str | None = None


class NfcScanRequest(BaseModel):
    card_id: str = Field(min_length=4, max_length=128)
    source: str = Field(default="phone_nfc", max_length=50)


class BalanceResponse(BaseModel):
    card_id: str
    balance: int


class TopUpRequest(BaseModel):
    card_id: str = Field(min_length=4)
    amount: int = Field(gt=0)


class ConfirmTopUpRequest(BaseModel):
    card_id: str = Field(min_length=4)
    code: str = Field(min_length=6, max_length=6)


class WithdrawRequest(BaseModel):
    card_id: str = Field(min_length=4)
    amount: int = Field(gt=0)
    pin: str = Field(min_length=4, max_length=12)
