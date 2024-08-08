from enum import Enum


class SearchModeEnum(Enum):
    local = 'local'
    global_ = 'global'


class DomainEnum(Enum):
    cypnest = 'cypnest'
    infotest = 'infotest'


class SourceEnum(Enum):
    chat = 'chat'
    qa = 'qa'
