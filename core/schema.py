from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import List
from enum import Enum

class HealthStatusEnum(str, Enum):
    OK = 'OK'
    ERROR = 'ERROR'
    UNKNOWN = 'UNKNOWN'

class HealthStatus(BaseModel):
    status: HealthStatusEnum = Field(description='health status')
    message: str = Field(description='status message')

class ErrorResponse(BaseModel):
    message: str = Field('', description='Error message')

class ScriptStartBodyModel(BaseModel):
    scriptName: str = Field(description='Name of custom script')
    scriptPath: str = Field(description='Relative path of custom script from custom script root directory')
    scriptHash: str = Field(description='SHA256 hash of custom script file')
    # service accepts empty inputs
    inputs: dict = Field({}, description='Dictionary of custom script inputs and corresponding values')
    # service accepts empty outputs
    outputs: dict = Field({}, description='Dictionary of custom script outputs')

    @field_validator('scriptPath')
    @classmethod
    def script_path_must_be_relative(cls, v:str)->str:
        if Path(v).is_absolute():
            raise ValueError('scriptPath must be relative path, not an absolute path')
        if ".." in Path(v).parts:
            raise ValueError('scriptPath must not include ..')
        if "~" in Path(v).parts:
            raise ValueError('scriptPath must not include ~')
        return v

class ScriptRunInfo(BaseModel):
    scriptRunId: str = Field(description='id of the running script')
    
class ScriptStatusBodyModel(BaseModel):
    scriptRunId: str = Field(description='custom script ID for the running custom script')

class CustomScriptStatus(str, Enum):
    PENDING = 'PENDING'
    ERROR = 'ERROR'
    PASS = 'PASS'
    FAIL = 'FAIL'

class VerificationStatus(str, Enum):
    PENDING = 'PENDING'
    ERROR = 'ERROR'
    PASS = 'PASS'
    FAIL = 'FAIL'

class ScriptEntriesModel(BaseModel):
    verification_status: VerificationStatus = Field(VerificationStatus.PENDING, 
        description='Verification status for the specified entry')
    entry_outputs: dict = Field({}, description='Custom script entry outputs')
    entry_output_array: List[dict] = Field([], description='Custom script entry output array')

class CustomScriptOutputs(BaseModel):
    outputs: dict = Field({}, description='Custom script outputs fields')
    output_array: List[dict] = Field([], description='Custom script output array')
    entries: ScriptEntriesModel = Field({}, description='Custom script entries')
    output_summary: str = Field('', description='human readable summary of output')

class ScriptStatusResp(BaseModel):
    logfile_url: str = Field('', description='Relative URL of download end point of logs. "custom_script/{script_run_id}/files"')
    logfile_path: str = Field('', description='The absolute path (on GDS host) to the custom script log file')
    custom_script_status: CustomScriptStatus = Field(CustomScriptStatus.PENDING, 
        description='The current status of the executed custom script')
    custom_script_outputs: CustomScriptOutputs = Field({}, 
        description='Object that contains all current output values from the executed custom script')
    logfile_lines: List[str] = Field([], description='last 25 lines of the custom script log file')

class ScriptHaltBodyModel(BaseModel):
    scriptRunId: str = Field(description='custom script ID for the running custom script')
