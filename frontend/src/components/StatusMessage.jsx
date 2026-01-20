/**
 * StatusMessage Component
 * Displays status messages with different types (success, error, loading)
 */

import React from 'react';

const StatusMessage = ({ status }) => {
    if (!status || !status.message) return null;

    return (
        <div className={`status ${status.type}`}>
            {status.message}
        </div>
    );
};

// Memoize to prevent unnecessary re-renders
export default React.memo(StatusMessage);
