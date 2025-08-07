// Mock implementation of @databricks/i18n
import React from "react";

export const FormattedMessage = ({
  defaultMessage,
  description,
}: {
  defaultMessage: string;
  description?: string;
}) => {
  return <>{defaultMessage}</>;
};

export const useI18n = () => {
  return {
    formatMessage: (descriptor: { defaultMessage: string }) => descriptor.defaultMessage,
  };
};
