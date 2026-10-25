-- Motorbike profile for Vietnam (Revision 9, Section 34 / M2).
--
-- Built on the stock OSRM car profile shipped in the image (/opt/car.lua,
-- OSRM v5.27.1) and overriding only what differs for a motorbike:
--   * access is resolved through the `motorcycle` tag hierarchy,
--     so `motorcycle=no` blocks a way and `motorcycle=yes` opens it;
--   * highway=motorway / motorway_link are never routable (VN expressways
--     forbid motorbikes);
--   * vehicle dimensions of a motorbike (narrow alleys, height barriers);
--   * free-flow speeds per highway class.
--
-- [NEEDS_VALIDATION: V-03] The speed table below is a provisional starting
-- point. It must be calibrated against ~20 Hanoi origin/destination pairs
-- during Phase 0-2 (MVP_CONFIG_BASELINE_V1 §6.1). Do not report these speeds
-- as measured values.

package.path = '/opt/?.lua;' .. package.path

local car = dofile('/opt/car.lua')

local function setup()
  local profile = car.setup()

  profile.vehicle_height = 1.5
  profile.vehicle_width  = 0.8
  profile.vehicle_length = 2.0
  profile.vehicle_weight = 250

  profile.access_tag_whitelist = Set {
    'yes', 'motorcycle', 'motor_vehicle', 'vehicle', 'permissive', 'designated'
  }
  profile.access_tags_hierarchy = Sequence {
    'motorcycle', 'motor_vehicle', 'vehicle', 'access'
  }
  profile.restrictions = Sequence {
    'motorcycle', 'motor_vehicle', 'vehicle'
  }

  -- WayHandlers.avoid_ways drops any way whose highway value is in this set.
  profile.avoid = Set {
    'area', 'reversible', 'impassable', 'hov_lanes', 'steps',
    'construction', 'proposed', 'motorway', 'motorway_link'
  }

  -- km/h, provisional (V-03). Motorway classes omitted: never routable.
  profile.speeds = Sequence {
    highway = {
      trunk           = 55,
      trunk_link      = 35,
      primary         = 45,
      primary_link    = 30,
      secondary       = 40,
      secondary_link  = 25,
      tertiary        = 35,
      tertiary_link   = 20,
      unclassified    = 30,
      residential     = 25,
      living_street   = 15,
      service         = 15
    }
  }

  return profile
end

return {
  setup = setup,
  process_way = car.process_way,
  process_node = car.process_node,
  process_turn = car.process_turn
}
