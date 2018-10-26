#pragma once

class ConfigNode {
 public:
  ConfigNode(ConfigNode *_parent, ConfigNode *_owner = nullptr)
      : owner(_parent->owner != nullptr ? _parent->owner : _parent),
        parent(_parent) {}
  ConfigNode *owner;
  ConfigNode *parent;
};

class ConfigTree {
 public:
  ConfigNode *root;
};
