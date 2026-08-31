/**
 * Fehlerarten, die der Mechaniker in der Oberfläche sehen kann.
 *
 * Netzwerk- und Backendfehler gehören bewusst nicht zu diesem lokalen
 * Fehlerzustands-System.
 */
export type FrontendErrorKind =
  | 'required'
  | 'invalid'
  | 'confirmation'
  | 'unexpected'

