import React, { useState, useEffect } from 'react';
import './ConfigAdmin.css';

interface Config {
  value: any;
  type: string;
  description: string;
  editable: boolean;
  required: boolean;
  full_key?: string;
}

interface ConfigCategory {
  [key: string]: Config;
}

interface AllConfigs {
  [category: string]: ConfigCategory;
}

export const ConfigAdmin: React.FC = () => {
  const [configs, setConfigs] = useState<AllConfigs>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editedValues, setEditedValues] = useState<{ [key: string]: any }>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [selectedConfigKey, setSelectedConfigKey] = useState<string | null>(null);
  const [showAuditLog, setShowAuditLog] = useState(false);

  // Fetch all configurations
  useEffect(() => {
    fetchConfigs();
  }, []);

  // Set first category as default
  useEffect(() => {
    if (Object.keys(configs).length > 0 && !selectedCategory) {
      setSelectedCategory(Object.keys(configs)[0]);
    }
  }, [configs, selectedCategory]);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8008/config/');
      if (!response.ok) throw new Error('Failed to fetch configurations');
      const data = await response.json();
      setConfigs(data.configurations);
      setEditedValues({});
    } catch (error) {
      showMessage('error', `Error loading configurations: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLog = async (categoryKey: string, paramKey: string) => {
    try {
      const response = await fetch(
        `http://localhost:8008/config/${categoryKey}/${paramKey}/audit?limit=50`
      );
      if (!response.ok) throw new Error('Failed to fetch audit log');
      const data = await response.json();
      setAuditLogs(data.logs);
      setShowAuditLog(true);
    } catch (error) {
      showMessage('error', `Error loading audit log: ${error}`);
    }
  };

  const handleValueChange = (key: string, value: any, configType: string) => {
    // Type conversion based on config type
    let convertedValue = value;
    if (configType === 'integer') {
      convertedValue = parseInt(value, 10);
    } else if (configType === 'float') {
      convertedValue = parseFloat(value);
    } else if (configType === 'boolean') {
      convertedValue = value === 'true' || value === true;
    } else if (configType === 'json' || configType === 'array') {
      try {
        convertedValue = JSON.parse(value);
      } catch {
        convertedValue = value;
      }
    }
    setEditedValues({ ...editedValues, [key]: convertedValue });
  };

  const handleSingleUpdate = async (categoryKey: string, paramKey: string) => {
    const fullKey = `${categoryKey}.${paramKey}`;
    const newValue = editedValues[fullKey];

    if (newValue === undefined) return;

    try {
      setSaving(true);
      const response = await fetch(
        `http://localhost:8008/config/${categoryKey}/${paramKey}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer admin_token`
          },
          body: JSON.stringify({
            value: newValue,
            reason: `Updated via admin panel`
          })
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update configuration');
      }

      showMessage('success', `Configuration updated successfully`);
      delete editedValues[fullKey];
      setEditedValues({ ...editedValues });
      fetchConfigs();
    } catch (error) {
      showMessage('error', `Error updating configuration: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  const handleBulkUpdate = async () => {
    if (Object.keys(editedValues).length === 0) {
      showMessage('error', 'No changes to save');
      return;
    }

    try {
      setSaving(true);
      const response = await fetch('http://localhost:8008/config/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer admin_token`
        },
        body: JSON.stringify({
          updates: editedValues,
          reason: 'Bulk update via admin panel'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update configurations');
      }

      showMessage('success', 'All configurations updated successfully');
      setEditedValues({});
      fetchConfigs();
    } catch (error) {
      showMessage('error', `Error updating configurations: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setEditedValues({});
    showMessage('success', 'Changes discarded');
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const renderConfigValue = (config: Config, key: string) => {
    const fullKey = selectedCategory ? `${selectedCategory}.${key}` : key;
    const currentValue = editedValues[fullKey] !== undefined ? editedValues[fullKey] : config.value;

    if (!config.editable) {
      return (
        <div className="value-display">
          <code>{JSON.stringify(currentValue)}</code>
          <span className="read-only-badge">Read-only</span>
        </div>
      );
    }

    switch (config.type) {
      case 'boolean':
        return (
          <select
            value={currentValue ? 'true' : 'false'}
            onChange={(e) => handleValueChange(fullKey, e.target.value, config.type)}
            className="config-input"
          >
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        );
      case 'integer':
      case 'float':
        return (
          <input
            type="number"
            value={currentValue}
            onChange={(e) => handleValueChange(fullKey, e.target.value, config.type)}
            className="config-input"
            step={config.type === 'float' ? '0.01' : '1'}
          />
        );
      case 'json':
      case 'array':
        return (
          <textarea
            value={typeof currentValue === 'string' ? currentValue : JSON.stringify(currentValue, null, 2)}
            onChange={(e) => handleValueChange(fullKey, e.target.value, config.type)}
            className="config-textarea"
            rows={6}
          />
        );
      case 'string':
      default:
        if (Array.isArray(currentValue)) {
          return (
            <textarea
              value={currentValue.join('\n')}
              onChange={(e) => handleValueChange(fullKey, e.target.value.split('\n'), config.type)}
              className="config-textarea"
              rows={3}
            />
          );
        }
        return (
          <input
            type="text"
            value={currentValue}
            onChange={(e) => handleValueChange(fullKey, e.target.value, config.type)}
            className="config-input"
          />
        );
    }
  };

  if (loading) {
    return <div className="config-admin loading">Loading configuration...</div>;
  }

  const categoryConfigs = selectedCategory ? configs[selectedCategory] : {};
  const hasChanges = Object.keys(editedValues).length > 0;

  return (
    <div className="config-admin">
      <div className="config-header">
        <h1>⚙️ System Configuration Manager</h1>
        <p>Manage system-wide configuration parameters without code changes</p>
      </div>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.type === 'success' ? '✓' : '⚠'} {message.text}
        </div>
      )}

      <div className="config-container">
        {/* Categories Sidebar */}
        <div className="categories-sidebar">
          <h3>Categories</h3>
          <div className="categories-list">
            {Object.keys(configs).map((category) => (
              <button
                key={category}
                className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                <span className="category-name">{category}</span>
                <span className="param-count">
                  {Object.keys(configs[category] || {}).length}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="config-content">
          {selectedCategory && (
            <>
              <div className="category-header">
                <h2>{selectedCategory.toUpperCase()}</h2>
                {hasChanges && (
                  <div className="unsaved-indicator">
                    {Object.keys(editedValues).length} unsaved change(s)
                  </div>
                )}
              </div>

              <div className="config-params">
                {Object.keys(categoryConfigs).map((paramKey) => {
                  const config = categoryConfigs[paramKey];
                  const fullKey = `${selectedCategory}.${paramKey}`;
                  const isEdited = editedValues[fullKey] !== undefined;

                  return (
                    <div key={paramKey} className={`config-item ${isEdited ? 'edited' : ''}`}>
                      <div className="config-item-header">
                        <div className="config-item-title">
                          <span className="param-key">{paramKey}</span>
                          <span className="param-type">{config.type}</span>
                          {config.required && <span className="required-badge">Required</span>}
                        </div>
                        <button
                          className="audit-btn"
                          onClick={() => {
                            setSelectedConfigKey(fullKey);
                            fetchAuditLog(selectedCategory, paramKey);
                          }}
                          title="View change history"
                        >
                          📋
                        </button>
                      </div>

                      <p className="param-description">{config.description}</p>

                      <div className="config-item-value">
                        {renderConfigValue(config, paramKey)}
                      </div>

                      {config.editable && (
                        <button
                          className="save-single-btn"
                          onClick={() => handleSingleUpdate(selectedCategory, paramKey)}
                          disabled={!isEdited || saving}
                        >
                          {isEdited ? '💾 Save' : '✓ Saved'}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              {hasChanges && (
                <div className="bulk-actions">
                  <button
                    className="save-all-btn"
                    onClick={handleBulkUpdate}
                    disabled={saving}
                  >
                    💾 Save All Changes ({Object.keys(editedValues).length})
                  </button>
                  <button className="reset-btn" onClick={handleReset} disabled={saving}>
                    ↻ Discard Changes
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Audit Log Modal */}
      {showAuditLog && (
        <div className="audit-modal" onClick={() => setShowAuditLog(false)}>
          <div className="audit-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="audit-header">
              <h3>Change History: {selectedConfigKey}</h3>
              <button className="close-btn" onClick={() => setShowAuditLog(false)}>
                ×
              </button>
            </div>

            <div className="audit-logs">
              {auditLogs.length > 0 ? (
                auditLogs.map((log) => (
                  <div key={log.id} className="audit-entry">
                    <div className="audit-meta">
                      <strong>{log.changed_by}</strong>
                      <span className="audit-date">
                        {new Date(log.changed_at).toLocaleString()}
                      </span>
                    </div>
                    {log.change_reason && (
                      <p className="audit-reason">{log.change_reason}</p>
                    )}
                    <div className="audit-values">
                      <div className="old-value">
                        <span>Before:</span>
                        <code>{JSON.stringify(log.old_value)}</code>
                      </div>
                      <div className="new-value">
                        <span>After:</span>
                        <code>{JSON.stringify(log.new_value)}</code>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="no-logs">No change history available</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfigAdmin;
