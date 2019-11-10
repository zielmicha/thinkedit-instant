;;; -*- lexical-binding: t -*-
(require 'json)
(require 'subr-x)

(make-variable-buffer-local 'instant/current-overlays)
(make-variable-buffer-local 'instant/state-overlay)
;(make-variable-buffer-local 'instant/run-command)

(defun instant/add-overlay (lineno text)
  (save-excursion
    (goto-line (+ 1 lineno))
    (backward-char 1)
    (let*
        ((formatted_text (concat "   " text "\n"))
         (text_length (length formatted_text))
         (ov (make-overlay (point) (1+ (point)) nil 'front-advance)))
      (add-to-list 'instant/current-overlays ov)
      (if (string-prefix-p "!" text)
          (add-face-text-property 0 text_length '(:foreground "red") nil formatted_text)
        (add-face-text-property 0 text_length '(:foreground "#333") nil formatted_text))
      (add-face-text-property 0 text_length '(:height 80) nil formatted_text)
      (overlay-put ov 'display formatted_text))))

(defun instant/run-for-filename (filename callback)
  (let* (
        (tempdir (string-trim (shell-command-to-string "mktemp -d")))
        (out-buffer (get-buffer-create "*thinkedit-instant-output*"))
        (p (make-process :name "thinkedit-instant-run" :buffer out-buffer :command (list "python3" "run_tracer.py" tempdir filename))))
    (set-process-sentinel p (lambda (p e) (instant/process-trace filename tempdir callback)))))

(defun instant/process-trace (filename tempdir callback)
  (let* (
         (out-buffer (get-buffer-create "*thinkedit-instant-output*"))
         (p (make-process :name "thinedit-instant-analyze" :buffer out-buffer :command
                          (list "python3" "analyze.py" (concat tempdir "/trace.json") (concat tempdir "/out.json")))))
    (set-process-sentinel
     p
     (lambda (p e)
       (if (file-exists-p (concat tempdir "/out.json"))
           (let ((data (json-read-file (concat tempdir "/out.json"))))
             (call-process-shell-command (concat "rm -r " tempdir))
             (funcall callback data))
         (progn
           (call-process-shell-command (concat "rm -r " tempdir))
           (message "thinkedit-instant failure, see *thinkedit-instant-output* buffer")))))))

(defun instant/refresh ()
  "refresh instant overlay"
  (interactive)
  (remove-overlays)
  (instant/run-for-filename
   buffer-file-name
   (lambda (result)
     (mapc (lambda (x) (instant/add-overlay (elt x 0) (elt x 1))) result))))

(defun instant-mode ()
  "instant-mode"
  (interactive)
  (add-hook 'after-save-hook 'instant/refresh nil t))

;; (let
;;     ((j (json-read-file "out.json")))
;;   (set-buffer (get-buffer "analyze.py"))
;;   (remove-overlays)
;;   (mapc (lambda (x) (print x) (instant/add-overlay (elt x 0) (elt x 1))) j))
;(instant/add-overlay 5 "  foo")
