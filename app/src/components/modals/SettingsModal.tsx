import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Save, X } from "lucide-react";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  initialRules?: string;
  onSave: (rules: string) => void;
}

const SettingsModal = ({ open, onClose, initialRules = "", onSave }: SettingsModalProps) => {
  const { t } = useTranslation();
  const [rules, setRules] = useState(initialRules);

  // Sync with prop changes
  useEffect(() => {
    setRules(initialRules);
  }, [initialRules]);

  const handleSave = () => {
    onSave(rules);
    onClose();
  };

  const handleClear = () => {
    setRules("");
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] bg-gray-900 text-white border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">{t('common.settings.title')}</DialogTitle>
          <DialogDescription className="text-gray-400">
            {t('common.settings.description')}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="rules" className="text-sm font-medium text-gray-200">
              {t('common.settings.rulesLabel')}
            </Label>
            <Textarea
              id="rules"
              placeholder={t('common.settings.placeholder')}
              value={rules}
              onChange={(e) => setRules(e.target.value)}
              className="min-h-[300px] bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-purple-500 focus:ring-purple-500"
            />
            <p className="text-xs text-gray-500">
              {t('common.settings.charactersCount', { count: rules.length })}
            </p>
          </div>

          <div className="bg-blue-900/20 border border-blue-800/30 rounded-lg p-3">
            <p className="text-xs text-blue-300">
              <strong>💡 {t('common.settings.tip')}:</strong> {t('common.settings.tipDescription')}
            </p>
          </div>
        </div>

        <div className="flex justify-between pt-4 border-t border-gray-700">
          <Button
            variant="outline"
            onClick={handleClear}
            className="border-gray-700 hover:bg-gray-800 hover:text-white"
          >
            <X className="w-4 h-4 mr-2" />
            {t('common.settings.clearRules')}
          </Button>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              className="border-gray-700 hover:bg-gray-800 hover:text-white"
            >
              {t('common.buttons.cancel')}
            </Button>
            <Button
              onClick={handleSave}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Save className="w-4 h-4 mr-2" />
              {t('common.settings.saveRules')}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SettingsModal;
