--
-- Prosody IM
-- Copyright (C) 2017 Marcel Waldvogel
--
-- This project is MIT/X11 licensed. Please see the
-- COPYING file in the source package for more information.
--

--
-- Behaves as if it were an lpty (Lua Pseudo TTY) object,
-- but connects through a socket. So it is a Pseudo-LPTY (pun intended).
--
-- To maximize fail-safety (and minimize modifications to the caller),
-- it auto-reconnects transparently.
--
-- Only provides the functions necessary for mod_auth_external.lua.
-- It follows a delegation pattern to the TCP socket in order to
-- simplify (re)connection.
--

local _M = {};
local plpty = {};

function _M.new(opts)
  -- create a new empty plpty object ignoring opts
  o = {}
  setmetatable(o, {__index = plpty});
  o.log = opts.log or print;
  return o;
end

function plpty:startproc(command)
  -- command may be of the form [@]<HOST>:<PORT> or <PORT>
  local host, port = string.match(command, "@?([^:]+):([^:]+)");
  log("debug", "local host=%s, port=%s", host, port);
  self.host = host or "localhost";
  self.port = port or command;
  log("debug", "self  host=%s, port=%s", self.host, self.port);
  return self:reconnect();
end

function plpty:hasproc()
  return self.connected;
end

function plpty:disconnect()
  if self.sock then
    self.sock:close();
  end
  self.connected = nil;
end

function plpty:reconnect()
  self:disconnect();
  self.sock = assert(require("socket").tcp(), "Cannot create TCP LuaSocket");
  self.connected, self.exitstr = self.sock:connect(self.host, self.port);
  if self.connected then
    self.log("info", "plpty:reconnect succeeded");
  else
    self.log("error", "plpty:reconnect failed: %s", self.exitstr);
  end
  return self.connected, self.exitstr;
end

function plpty:exitstatus()
  return self.exitstr, self.exitint or 0;
end

function plpty:send(text)
  self.log("debug", "plpty:send(%s)", text);

  -- sock:send() will not check for closedness
  local ok, err = self:read(0);
  if not ok and not (err ~= "timeout") then
    self:reconnect();
  end

  local bytes, err = self.sock:send(text);
  self.log("debug", "bytes=%s, err=%s", bytes or "nil", err or "---");
  if err then
    self.log("info", "plpty:send: socket to %s:%s %s", self.host, self.port, err);
    if self:reconnect() then
      -- retransmit
      bytes, err = self.sock:send(text);
    end
  end
end

function plpty:flush(mode)
  -- noop
end

function plpty:getfd()
  return self.sock:getfd();
end

function plpty:read(timeout)
  self.sock:settimeout(timeout);
  local ok, err = self.sock:receive();
  self.log("debug", "plpty:read(%d) -> %s, %s", timeout, ok or "---", err or "---");
  if err then
    self.log("info", "plpty:read: socket to %s:%s %s", self.host, self.port, err);
    self:disconnect();
  end
  return ok;
end

return _M;
