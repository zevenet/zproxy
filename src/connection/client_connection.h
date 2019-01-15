//
// Created by abdess on 1/11/19.
//
#pragma once
#include "connection.h"
#include "../stats/counter.h"

class ClientConnection : public Connection , public Counter<ClientConnection> {

};


