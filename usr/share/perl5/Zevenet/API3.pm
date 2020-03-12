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

include 'Zevenet::API3::Certificate';
include 'Zevenet::API3::Certificate::Activation';
include 'Zevenet::API3::Certificate::Farm';
include 'Zevenet::API3::Farm::Delete';
include 'Zevenet::API3::Farm::Action';
include 'Zevenet::API3::Farm::Guardian';
include 'Zevenet::API3::Farm::Get';
include 'Zevenet::API3::Farm::Post';
include 'Zevenet::API3::Farm::Put';
include 'Zevenet::API3::Interface';
include 'Zevenet::API3::System';
include 'Zevenet::API3::System::Cluster';
include 'Zevenet::API3::Stats';
include 'Zevenet::API3::Graph';

1;

