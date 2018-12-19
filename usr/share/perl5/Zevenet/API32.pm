#!/usr/bin/perl
###############################################################################
#
#    Zevenet Software License
#    This file is part of the Zevenet Load Balancer software package.
#
#    Copyright (C) 2014-today ZEVENET SL, Sevilla (Spain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

use strict;

use Zevenet::API32::Certificate;
use Zevenet::API32::Certificate::Farm;
use Zevenet::API32::Farm::Delete;
use Zevenet::API32::Farm::Action;
use Zevenet::API32::Farm::Guardian;
use Zevenet::API32::Farm::Get;
use Zevenet::API32::Farm::Post;
use Zevenet::API32::Farm::Put;
use Zevenet::API32::Interface;
use Zevenet::API32::System;
use Zevenet::API32::Stats;
use Zevenet::API32::Graph;

1;