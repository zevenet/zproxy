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

use Zevenet::Net;

use Zevenet::Farm::GSLB::Config;
use Zevenet::Farm::GSLB::Action;
use Zevenet::Farm::GSLB::Factory;
use Zevenet::Farm::GSLB::Validate;
use Zevenet::Farm::GSLB::Service;
use Zevenet::Farm::GSLB::Backend;
use Zevenet::Farm::GSLB::Zone;
use Zevenet::Farm::GSLB::Stats;
use Zevenet::Farm::GSLB::FarmGuardian;

1;
