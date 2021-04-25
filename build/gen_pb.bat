if exist ..\src\ImgProc (
    ..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --cpp_out ../src/ImgProc/Protobuf/ ../protocol/common.proto
    ..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --cpp_out ../src/ImgProc/Protobuf/ ../protocol/gameregProtoc.proto
)

if exist ..\tools\SDKTool\src\communicate\protocol (
    ..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../tools/SDKTool/src/communicate/protocol/ ../protocol/common.proto
    ..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../tools/SDKTool/src/communicate/protocol/ ../protocol/gameregProtoc.proto
)

..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/ManageCenter/pyManageCenter/protocol/ ../protocol/common.proto
..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/ManageCenter/pyManageCenter/protocol/ ../protocol/gameregProtoc.proto
..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/IOService/pyIOService/protocol/ ../protocol/common.proto
..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/IOService/pyIOService/protocol/ ../protocol/gameregProtoc.proto
..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/API/AgentAPI/protocol/ ../protocol/common.proto
..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/API/AgentAPI/protocol/ ../protocol/gameregProtoc.proto
..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/AgentAI/protocol/ ../protocol/common.proto
..\Modules\protobuf\Windows\x64\bin\protoc -I ../protocol --python_out ../src/AgentAI/protocol/ ../protocol/gameregProtoc.proto
