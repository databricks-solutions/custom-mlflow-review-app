import React, { useMemo } from "react";
import { RawIntlProvider, createIntl, createIntlCache } from "react-intl";

// Comprehensive messages for MLflow TracesView component
const messages = {
  // Trace view messages
  "trace.view.title": "Trace View",
  "trace.view.request": "Request",
  "trace.view.response": "Response",
  "trace.view.duration": "Duration",
  "trace.view.status": "Status",
  "trace.view.timestamp": "Timestamp",
  "trace.view.spans": "Spans",
  "trace.view.details": "Details",
  "trace.view.metadata": "Metadata",
  "trace.view.loading": "Loading...",
  "trace.view.error": "Error loading trace",
  "trace.view.noData": "No traces found",
  "trace.view.empty": "No traces to display",

  // MLflow specific messages
  "mlflow.traces.title": "Traces",
  "mlflow.traces.view": "Traces View",
  "mlflow.traces.loading": "Loading traces...",
  "mlflow.traces.empty": "No traces found",
  "mlflow.traces.error": "Error loading traces",
  "mlflow.traces.search": "Search traces",
  "mlflow.traces.filter": "Filter traces",
  "mlflow.traces.refresh": "Refresh traces",
  "mlflow.traces.table.name": "Name",
  "mlflow.traces.table.timestamp": "Timestamp",
  "mlflow.traces.table.duration": "Duration",
  "mlflow.traces.table.status": "Status",
  "mlflow.traces.table.id": "Trace ID",
  "mlflow.traces.table.experiment": "Experiment",
  "mlflow.traces.table.run": "Run",
  "mlflow.traces.table.user": "User",
  "mlflow.traces.table.tags": "Tags",
  "mlflow.traces.table.request": "Request",
  "mlflow.traces.table.response": "Response",
  "mlflow.traces.table.spans": "Spans",
  "mlflow.traces.table.inputs": "Inputs",
  "mlflow.traces.table.outputs": "Outputs",

  // Experiment tracking messages
  "experiment.view.title": "Experiment View",
  "experiment.runs.title": "Runs",
  "experiment.artifacts.title": "Artifacts",
  "experiment.metrics.title": "Metrics",
  "experiment.params.title": "Parameters",
  "experiment.tags.title": "Tags",

  // Common UI messages
  "common.loading": "Loading...",
  "common.error": "Error",
  "common.retry": "Retry",
  "common.close": "Close",
  "common.open": "Open",
  "common.ok": "OK",
  "common.cancel": "Cancel",
  "common.save": "Save",
  "common.delete": "Delete",
  "common.edit": "Edit",
  "common.view": "View",
  "common.copy": "Copy",
  "common.search": "Search",
  "common.filter": "Filter",
  "common.sort": "Sort",
  "common.refresh": "Refresh",
  "common.clear": "Clear",
  "common.reset": "Reset",
  "common.apply": "Apply",
  "common.submit": "Submit",
  "common.download": "Download",
  "common.upload": "Upload",
  "common.expand": "Expand",
  "common.collapse": "Collapse",
  "common.show": "Show",
  "common.hide": "Hide",
  "common.next": "Next",
  "common.previous": "Previous",
  "common.first": "First",
  "common.last": "Last",
  "common.all": "All",
  "common.none": "None",
  "common.select": "Select",
  "common.deselect": "Deselect",
  "common.name": "Name",
  "common.value": "Value",
  "common.type": "Type",
  "common.description": "Description",
  "common.created": "Created",
  "common.updated": "Updated",
  "common.modified": "Modified",
  "common.size": "Size",
  "common.count": "Count",
  "common.total": "Total",
  "common.average": "Average",
  "common.minimum": "Minimum",
  "common.maximum": "Maximum",
  "common.sum": "Sum",
  "common.yes": "Yes",
  "common.no": "No",
  "common.true": "True",
  "common.false": "False",
  "common.enabled": "Enabled",
  "common.disabled": "Disabled",
  "common.active": "Active",
  "common.inactive": "Inactive",
  "common.success": "Success",
  "common.failed": "Failed",
  "common.pending": "Pending",
  "common.running": "Running",
  "common.completed": "Completed",
  "common.cancelled": "Cancelled",

  // Table messages
  "table.noData": "No data available",
  "table.loading": "Loading data...",
  "table.empty": "No items to display",
  "table.rows": "rows",
  "table.page": "Page",
  "table.of": "of",
  "table.rowsPerPage": "Rows per page",
  "table.firstPage": "First page",
  "table.lastPage": "Last page",
  "table.nextPage": "Next page",
  "table.previousPage": "Previous page",

  // Modal messages
  "modal.close": "Close",
  "modal.title": "Modal",

  // Form messages
  "form.required": "Required",
  "form.optional": "Optional",
  "form.invalid": "Invalid",
  "form.valid": "Valid",
  "form.placeholder": "Enter value...",

  // Date/time messages
  "date.format": "{date}",
  "time.format": "{time}",
  "datetime.format": "{date} {time}",
  "duration.ms": "{value}ms",
  "duration.s": "{value}s",
  "duration.m": "{value}m",
  "duration.h": "{value}h",
  "duration.d": "{value}d",

  // Status messages
  "status.ok": "OK",
  "status.error": "Error",
  "status.warning": "Warning",
  "status.info": "Info",
  "status.success": "Success",
  "status.failed": "Failed",
  "status.pending": "Pending",
  "status.running": "Running",
  "status.completed": "Completed",
  "status.cancelled": "Cancelled",
  "status.unknown": "Unknown",

  // Error messages
  "error.generic": "An error occurred",
  "error.network": "Network error",
  "error.timeout": "Request timeout",
  "error.notFound": "Not found",
  "error.unauthorized": "Unauthorized",
  "error.forbidden": "Forbidden",
  "error.serverError": "Server error",
  "error.badRequest": "Bad request",
  "error.validation": "Validation error",

  // Empty states
  "empty.noResults": "No results found",
  "empty.noItems": "No items",
  "empty.noData": "No data",
  "empty.noContent": "No content",
  "empty.notFound": "Not found",
};

// MLflow-compatible IntlProvider using the exact same pattern as MLflow OSS
export const ReactIntlProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const intl = useMemo(() => {
    // Create intl cache like MLflow does
    const cache = createIntlCache();

    // Create intl object exactly like MLflow's pattern
    const baseIntl = createIntl(
      {
        locale: "en",
        messages: {}, // MLflow uses empty messages object and relies on defaultMessage
        defaultLocale: "en",
      },
      cache
    );

    // Override formatMessage to handle MLflow's pattern gracefully
    const originalFormatMessage = baseIntl.formatMessage.bind(baseIntl);

    baseIntl.formatMessage = (descriptor: any, values?: any, opts?: any) => {
      // Handle various descriptor formats MLflow uses
      if (!descriptor) {
        return "";
      }

      // Handle string descriptors
      if (typeof descriptor === "string") {
        return descriptor;
      }

      // Handle MLflow's descriptor objects
      if (typeof descriptor === "object") {
        // If it has defaultMessage, use it (MLflow pattern)
        if (descriptor.defaultMessage) {
          return descriptor.defaultMessage;
        }

        // If it has message property
        if (descriptor.message) {
          return descriptor.message;
        }

        // If it has id but no defaultMessage, try to format it
        if (descriptor.id) {
          try {
            return originalFormatMessage(descriptor, values, opts);
          } catch (error) {
            return descriptor.id;
          }
        }
      }

      return "";
    };

    return baseIntl;
  }, []);

  return <RawIntlProvider value={intl}>{children}</RawIntlProvider>;
};
