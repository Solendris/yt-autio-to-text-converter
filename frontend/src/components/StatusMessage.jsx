import React from 'react';

const StatusMessage = ({ status }) => {
    if (!status || !status.message) return null;

    return (
        <div className={`status ${status.type}`}>
            {status.message}
        </div>
    );
};

export default StatusMessage;
