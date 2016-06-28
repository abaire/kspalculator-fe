#!/usr/bin/env python

import json
import os
from collections import namedtuple

import jinja2
import webapp2

from kspalculator.bodies import CelestialBody, Location, CalculateCost
from kspalculator.finder import Finder
from kspalculator.parts import RadialSize


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True,
    trim_blocks=True)


DesignVals = namedtuple('DesignVals', ['name', 'mass', 'cost', 'liquid_fuel_units', 'liquid_fuel',
                                       'special_fuel_type', 'special_fuel_units', 'special_fuel',
                                       'required', 'radial_size', 'gimbal', 'electricity',
                                       'min_strut_required', 'notes_list', 'per_stage_performance'])
StagePerformance = namedtuple('StagePerformance',
                              ['solid_booster', 'delta_v', 'pressure', 'acc_start', 'acc_end',
                               'mass_start', 'mass_end'])


class MainPage(webapp2.RequestHandler):
    """Handler for the main page."""

    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({
            'body_options': sorted([b.name for b in CelestialBody]),
            'location_options': sorted([l.name for l in Location]),
        }))

    def post(self):
        payload = int(self.request.get('payload'))
        radial_size = self._ParsePreferredRadialSize(self.request.get('preferred-radius', None))
        ordering = self.request.get('ordering')
        preferences = self.request.get_all('preferences')
        gimbal = int(self.request.get('gimbal'))

        velocities = map(float, self.request.get_all('delta-v'))
        accelerations = map(float, self.request.get_all('acceleration'))
        pressures = map(lambda x: float(x) / 100.0, self.request.get_all('pressure'))

        f = Finder(payload,
                   radial_size,
                   velocities,
                   accelerations,
                   pressures,
                   gimbal,
                   'boosters' in preferences,
                   'electricity' in preferences,
                   'length' in preferences)
        designs = f.Find(best_only=True,
                         order_by_cost=(ordering == 'cost'))
        template = JINJA_ENVIRONMENT.get_template('searchResults.html')
        response_body = template.render({
            'results': map(self._PrepareDesignForTemplate, designs),
        })
        self.response.write(response_body)

    def _PrepareDesignForTemplate(self, design):
        """Converts a Design to a tuple for the searchResults template."""
        if design.mainenginecount == 1:
            name = design.mainengine.name
        else:
            name = '(%i) %s, radially mounted' % (design.mainenginecount, design.mainengine.name)

        if design.liquidfuel:
            liquid_fuel_units = design.liquidfuel * 8.0 / 9.0 * 0.2
        else:
            liquid_fuel_units = None

        if design.specialfuel:
            unit_mass = float(design.specialfuelunitmass)
            special_fuel_units = design.specialfuel / (design.mainengine.f_e + 1.0) / unit_mass
        else:
            special_fuel_units = None

        if design.sfb is None:
            required = design.mainengine.level.name
        else:
            if design.sfb.level.DependsOn(design.mainengine.level):
                required = design.sfb.level.name
            elif design.mainengine.level.DependsOn(design.sfb.level):
                required = design.mainengine.level.name
            else:
                required = "%s and %s" % (design.sfb.level.name, design.mainengine.level.name)

        if design.mainengine.length == 0:
            min_strut_required = "LT-05 Micro Landing Struts"
        elif design.mainengine.length == 1:
            min_strut_required = "LT-1 Landing Struts"
        elif design.mainengine.length == 2:
            min_strut_required = "LT-2 Landing Struts"
        else:
            min_strut_required = None

        per_stage_performance = self._PrepareStagePerformanceListForTemplate(design)
        return DesignVals(name, design.mass, design.cost, liquid_fuel_units, design.liquidfuel,
                          design.specialfueltype, special_fuel_units, design.specialfuel, required,
                          design.size.name, design.mainengine.tvc, design.mainengine.electricity,
                          min_strut_required, design.notes, per_stage_performance)

    def _PrepareStagePerformanceListForTemplate(self, design):
        delta_v, pressure, acc_start, acc_end, mass_start, mass_end, solid, _ = design.performance
        num_stages = len(delta_v)
        phases = []
        for i in range(num_stages):
            phases.append(StagePerformance(solid[i],
                                           delta_v[i],
                                           pressure[i],
                                           acc_start[i],
                                           acc_end[i],
                                           mass_start[i] / 1000.0,
                                           mass_end[i] / 1000.0))
        return phases

    def _ParsePreferredRadialSize(self, value_str):
        if value_str == 'tiny':
            return RadialSize.Tiny
        elif value_str == 'small':
            return RadialSize.Small
        elif value_str == 'large':
            return RadialSize.Large
        elif value_str == 'extralarge':
            return RadialSize.ExtraLarge
        return None

class TransferStageCalculatorPage(webapp2.RequestHandler):
    """Handler for the transfer stage resolver."""

    def post(self):
        start_body_name = self.request.get('start_body')
        start_location_name = self.request.get('start_location')
        end_body_name = self.request.get('end_body')
        end_location_name = self.request.get('end_location')

        response_body = {}
        try:
            start_body = CelestialBody.__members__[start_body_name]
            start_location = Location.__members__[start_location_name]
            end_body = CelestialBody.__members__[end_body_name]
            end_location = Location.__members__[end_location_name]

            delta_vs, accelerations, pressures = CalculateCost(start_body, start_location,
                                                               end_body, end_location)
            response_body['delta_vs'] = delta_vs
            response_body['accelerations'] = accelerations
            response_body['pressures'] = pressures
        except:
            response_body['error'] = 'Failed to parse arguments.'

        self.response.write(json.dumps(response_body))


app = webapp2.WSGIApplication(
    [
        ('/', MainPage),
        ('/search', MainPage),
        ('/transferstages', TransferStageCalculatorPage)
    ],
    debug=True)
